from typing import Dict, List, Literal, Optional, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.chart.types import CollectionChartDefinition
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
from forestadmin.datasource_toolkit.decorators.hook.types import CrudMethod, HookHandler, Position
from forestadmin.datasource_toolkit.decorators.operators_emulate.types import OperatorDefinition
from forestadmin.datasource_toolkit.decorators.relation.types import (
    PartialManyToMany,
    PartialManyToOne,
    PartialOneToMany,
    PartialOneToOne,
    RelationDefinition,
)
from forestadmin.datasource_toolkit.decorators.search.collections import SearchDefinition
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentAlias
from forestadmin.datasource_toolkit.decorators.write.write_replace.types import WriteDefinition
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType, Validation
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.plugins.add_external_relation import AddExternalRelation, AddExternalRelationOptions
from forestadmin.datasource_toolkit.plugins.import_field import ImportField, ImportFieldOption
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils, CollectionUtilsException
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE
from typing_extensions import Self


class CollectionCustomizer:
    def __init__(
        self, datasource_customizer: "DatasourceCustomizer", stack: DecoratorStack, collection_name: str  # noqa: F821
    ):
        self.datasource_customizer = datasource_customizer
        self.stack = stack
        self.collection_name = collection_name

    @property
    def schema(self) -> CollectionSchema:
        return self.stack.validation.get_collection(self.collection_name).schema

    def add_action(self, name: str, action: ActionDict) -> Self:
        async def _add_action():
            self.stack.action.get_collection(self.collection_name).add_action(name, action)

        self.stack.queue_customization(_add_action)
        return self

    def add_segment(self, name: str, segment: SegmentAlias) -> Self:
        async def _add_segment():
            self.stack.segment.get_collection(self.collection_name).add_segment(name, segment)

        self.stack.queue_customization(_add_segment)
        return self

    def rename_field(self, current_name: str, new_name: str) -> Self:
        async def _rename_field():
            self.stack.rename_field.get_collection(self.collection_name).rename_field(current_name, new_name)

        self.stack.queue_customization(_rename_field)
        return self

    def add_field(self, name: str, computed_definition: ComputedDefinition) -> Self:
        async def _add_field():
            collection_before_relations = self.stack.early_computed.get_collection(self.collection_name)
            collection_after_relations = self.stack.late_computed.get_collection(self.collection_name)
            can_be_compted_before_relations = True
            for dependency in computed_definition["dependencies"]:
                try:
                    CollectionUtils.get_field_schema(collection_before_relations, dependency)
                except CollectionUtilsException:
                    can_be_compted_before_relations = False
                    break

            collection = collection_before_relations if can_be_compted_before_relations else collection_after_relations
            collection.register_computed(name, computed_definition)

        self.stack.queue_customization(_add_field)
        return self

    def add_validation(self, name: str, validation: Validation) -> Self:
        ForestLogger.log("warning", "'add_validation' is deprecated, please use 'add_field_validation' instead")
        return self.add_field_validation(name, validation)

    def add_field_validation(self, name: str, validation: Validation) -> Self:
        async def _add_validation():
            self.stack.validation.get_collection(self.collection_name).add_validation(name, validation)

        self.stack.queue_customization(_add_validation)
        return self

    def disable_count(self) -> Self:
        async def _disable_count():
            self.stack.schema.get_collection(self.collection_name).override_schema("countable", False)

        self.stack.queue_customization(_disable_count)
        return self

    def remove_field(self, *fields) -> Self:
        async def _remove_field():
            stack_collection = self.stack.publication.get_collection(self.collection_name)
            for field in fields:
                stack_collection.change_field_visibility(field, False)

        self.stack.queue_customization(_remove_field)
        return self

    def replace_search(self, definition: SearchDefinition) -> Self:
        async def _replace_search():
            self.stack.search.get_collection(self.collection_name).replace_search(definition)

        self.stack.queue_customization(_replace_search)
        return self

    def add_chart(self, name: str, definition: CollectionChartDefinition) -> Self:
        async def _add_chart():
            self.stack.chart.get_collection(self.collection_name).add_chart(name, definition)

        self.stack.queue_customization(_add_chart)
        return self

    def replace_field_writing(self, name: str, definition: WriteDefinition) -> Self:
        async def _replace_field_writing():
            self.stack.write.get_collection(self.collection_name).replace_field_writing(name, definition)

        self.stack.queue_customization(_replace_field_writing)
        return self

    def replace_field_operator(self, name: str, operator: Operator, replacer: OperatorDefinition) -> Self:
        async def _replace_field_operator():
            if self.stack.early_op_emulate.get_collection(self.collection_name).schema["fields"].get(name) is not None:
                collection = self.stack.early_op_emulate.get_collection(self.collection_name)
            else:
                collection = self.stack.late_op_emulate.get_collection(self.collection_name)
            collection.replace_field_operator(name, operator, replacer)

        self.stack.queue_customization(_replace_field_operator)
        return self

    def emulate_field_operator(self, name: str, operator: Operator) -> Self:
        async def _emulate_field_operator():
            if self.stack.early_op_emulate.get_collection(self.collection_name).schema["fields"].get(name) is not None:
                collection = self.stack.early_op_emulate.get_collection(self.collection_name)
            else:
                collection = self.stack.late_op_emulate.get_collection(self.collection_name)
            collection.emulate_field_operator(name, operator)

        self.stack.queue_customization(_emulate_field_operator)
        return self

    def emulate_field_filtering(self, name: str) -> Self:
        async def _emulate_field_filtering():
            collection = self.stack.late_op_emulate.get_collection(self.collection_name)
            field = collection.schema["fields"][name]
            operators = MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[field["column_type"]]

            if field["column_type"] == PrimitiveType.STRING:
                for operator in operators:
                    if operator not in field.get("filter_operators", {}):
                        self.emulate_field_operator(name, operator)

        self.stack.queue_customization(_emulate_field_filtering)
        return self

    def add_many_to_one_relation(
        self, name: str, foreign_collection: str, foreign_key: str, foreign_key_target: Optional[str] = None
    ) -> Self:
        self._add_relation(
            name,
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection=foreign_collection,
                foreign_key=foreign_key,
                foreign_key_target=foreign_key_target,
            ),
        )
        return self

    def add_one_to_many_relation(
        self, name: str, foreign_collection: str, origin_key: str, origin_key_target: Optional[str] = None
    ) -> Self:
        self._add_relation(
            name,
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection=foreign_collection,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
            ),
        )
        return self

    def add_one_to_one_relation(
        self, name: str, foreign_collection: str, origin_key: str, origin_key_target: Optional[str] = None
    ) -> Self:
        self._add_relation(
            name,
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection=foreign_collection,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
            ),
        )
        return self

    def add_many_to_many_relation(
        self,
        name: str,
        foreign_collection: str,
        through_collection: str,
        origin_key: str,
        foreign_key: str,
        origin_key_target: Optional[str] = None,
        foreign_key_target: Optional[str] = None,
    ) -> Self:
        self._add_relation(
            name,
            PartialManyToMany(
                type=FieldType.MANY_TO_MANY,
                foreign_collection=foreign_collection,
                through_collection=through_collection,
                origin_key=origin_key,
                foreign_key=foreign_key,
                origin_key_target=origin_key_target,
                foreign_key_target=foreign_key_target,
            ),
        )
        return self

    def _add_relation(self, name: str, definition: RelationDefinition) -> Self:
        async def __add_relation():
            self.stack.relation.get_collection(self.collection_name).add_relation(name, definition)

        self.stack.queue_customization(__add_relation)
        return self

    def add_hook(self, position: Position, type: CrudMethod, handler: HookHandler) -> Self:
        async def _add_hook():
            self.stack.hook.get_collection(self.collection_name).add_hook(position, type, handler)

        self.stack.queue_customization(_add_hook)
        return self

    def emulate_field_sorting(self, name: str) -> Self:
        async def _emulate_field_sorting():
            self.stack.sort_emulate.get_collection(self.collection_name).emulate_field_sorting(name)

        self.stack.queue_customization(_emulate_field_sorting)
        return self

    def replace_field_sorting(self, name: str, equivalent_sort: List[PlainSortClause]) -> Self:
        async def _replace_field_sorting():
            self.stack.sort_emulate.get_collection(self.collection_name).replace_field_sorting(name, equivalent_sort)

        self.stack.queue_customization(_replace_field_sorting)
        return self

    def replace_field_binary_mode(self, name: str, binary_mode: Union[Literal["datauri"], Literal["hex"]]) -> Self:
        async def _replace_field_binary_mode():
            self.stack.binary.get_collection(self.collection_name).set_binary_mode(name, binary_mode)

        self.stack.queue_customization(_replace_field_binary_mode)

    def use(self, plugin: type, options: Optional[Dict] = {}) -> Self:
        async def _use():
            await plugin().run(self.datasource_customizer, self, options)

        self.stack.queue_customization(_use)
        return self

    def import_field(self, name: str, options: ImportFieldOption) -> Self:
        self.use(ImportField, {"name": name, **options})
        return self

    def add_external_relation(self, name: str, definition: AddExternalRelationOptions) -> Self:
        self.use(AddExternalRelation, {"name": name, **definition})
        return self
