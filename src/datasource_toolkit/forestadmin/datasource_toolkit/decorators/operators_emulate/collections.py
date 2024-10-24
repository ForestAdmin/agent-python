from typing import Dict, List, Optional, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.operators_emulate.types import OperatorDefinition
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, Operator, RelationAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function
from forestadmin.datasource_toolkit.validations.condition_tree import ConditionTreeValidator
from forestadmin.datasource_toolkit.validations.field import FieldValidator
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class OperatorsEmulateCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource):
        self._fields: Dict[str, Dict[Operator, Optional[OperatorDefinition]]] = {}
        super().__init__(collection, datasource)

    def emulate_field_operator(self, name: str, operator: Operator):
        self.replace_field_operator(name, operator, None)

    def replace_field_operator(self, name: str, operator: Operator, replace_by: Optional[OperatorDefinition]):
        # Check that the collection can actually support our rewriting
        pks = SchemaUtils.get_primary_keys(self.child_collection.schema)
        for pk in pks:
            schema = self.child_collection.schema["fields"].get(pk)
            operators = schema["filter_operators"]

            if Operator.EQUAL not in operators or Operator.IN not in operators:
                raise ForestException(
                    f"Cannot override operators on collection '{self.name}': the primary key columns must"
                    + " support 'Equal' and 'In' operators"
                )

        # Check that targeted field is valid
        FieldValidator.validate(self, name)

        field = self.child_collection.schema["fields"].get(name)
        if field is None:
            raise ForestException(f"Cannot replace operator for relation on field '{name}'")

        if operator not in MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE.get(self.schema["fields"][name]["column_type"], []):
            raise ForestException(
                f"Cannot replace operator '{operator.value}' on field "
                f"type '{self.schema['fields'][name]['column_type'].value}' for field '{name}'."
            )

        if self._fields.get(name) is None:
            self._fields[name] = dict()
        self._fields[name][Operator(operator)] = replace_by
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        fields: Dict[str, FieldAlias] = {}

        for name, schema in sub_schema["fields"].items():
            if name in self._fields:
                fields[name] = {
                    **schema,
                    "filter_operators": set([*schema["filter_operators"], *self._fields.get(name, []).keys()]),
                }
            else:
                fields[name] = {**schema}
        return {**sub_schema, "fields": fields}

    async def _refine_filter(
        self, caller: User, _filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        if _filter is None or _filter.condition_tree is None:
            return _filter

        async def _replace_async_handler(leaf):
            return await self.replace_leaf(caller, leaf, [])

        return _filter.override({"condition_tree": await _filter.condition_tree.replace_async(_replace_async_handler)})

    async def replace_leaf(self, caller: User, leaf: ConditionTreeLeaf, replacement: List[str]) -> ConditionTree:
        # ConditionTree is targeting a field on another collection => recurse.
        if ":" in leaf.field:
            prefix = leaf.field.split(":")[0]
            schema: RelationAlias = self.schema["fields"][prefix]
            association = self.datasource.get_collection(schema["foreign_collection"])

            async def replace_async_handler(sub_leaf):
                return await association.replace_leaf(caller, sub_leaf, replacement)

            association_leaf = await leaf.unnest().replace_async(replace_async_handler)
            return association_leaf.nest(prefix)

        if leaf.operator in self._fields.get(leaf.field, {}):
            return await self.compute_equivalent(caller, leaf, replacement)
        else:
            return leaf

    async def compute_equivalent(self, caller: User, leaf: ConditionTreeLeaf, replacements: List[str]) -> ConditionTree:
        handler = self._fields.get(leaf.field, {}).get(leaf.operator)

        if handler is not None:
            replacement_id = f"{self.name}.{leaf.field}[{leaf.operator}]"
            sub_replacements = [*replacements, replacement_id]

            if replacement_id in replacements:
                raise ForestException(f"Operator replacement cycle: {' -> '.join(sub_replacements)}")

            result = await call_user_function(handler, leaf.value, CollectionCustomizationContext(self, caller))

            if result:
                equivalent = (
                    result if isinstance(result, ConditionTree) else ConditionTreeFactory.from_plain_object(result)
                )

                async def replace_leaf_handler(sub_leaf):
                    return await self.replace_leaf(caller, sub_leaf, sub_replacements)

                equivalent = await equivalent.replace_async(replace_leaf_handler)

                ConditionTreeValidator.validate(equivalent, self)
                return equivalent

        # Query all records on the dataSource and emulate the filter.
        return ConditionTreeFactory.match_records(
            self.schema,
            leaf.filter(
                await self.list(caller, PaginatedFilter({}), leaf.projection.with_pks(self)), self, caller.timezone
            ),
        )
