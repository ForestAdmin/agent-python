from typing import List, Optional

from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionAlias
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
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils, CollectionUtilsException
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class CollectionCustomizer:
    def __init__(
        self, datasource_customizer: "DatasourceCustomizer", stack: DecoratorStack, collection_name: str  # noqa: F821
    ):
        self.datasource_customizer = datasource_customizer
        self.stack = stack
        self.collection_name = collection_name

    def add_action(self, name: str, action: ActionAlias):
        self.stack.action.get_collection(self.collection_name).add_action(name, action)

    def add_segment(self, name: str, segment: SegmentAlias):
        self.stack.segment.get_collection(self.collection_name).add_segment(name, segment)

    def rename_field(self, current_name: str, new_name: str):
        self.stack.rename_field.get_collection(self.collection_name).rename_field(current_name, new_name)

    def add_field(self, name: str, computed_definition: ComputedDefinition):
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

    def add_validation(self, name: str, validation: List):
        self.stack.validation.get_collection(self.collection_name).add_validation(name, validation)

    def disable_count(self):
        self.stack.schema.get_collection(self.collection_name).override_schema("countable", False)

    def remove_field(self, *fields):
        stack_collection = self.stack.publication.get_collection(self.collection_name)
        for field in fields:
            stack_collection.change_field_visibility(field, False)

    def replace_search(self, definition: SearchDefinition):
        self.stack.search.get_collection(self.collection_name).replace_search(definition)

    def add_chart(self, name: str, definition: CollectionChartDefinition):
        self.stack.chart.get_collection(self.collection_name).add_chart(name, definition)

    def replace_field_writing(self, name: str, definition: WriteDefinition):
        self.stack.write.get_collection(self.collection_name).replace_field_writing(name, definition)

    def replace_field_operator(self, name: str, operator: Operator, replacer: OperatorDefinition):
        if self.stack.early_op_emulate.get_collection(self.collection_name).schema["fields"].get(name) is not None:
            collection = self.stack.early_op_emulate.get_collection(self.collection_name)
        else:
            collection = self.stack.late_op_emulate.get_collection(self.collection_name)
        collection.replace_field_operator(name, operator, replacer)

    def emulate_field_operator(self, name: str, operator: Operator):
        if self.stack.early_op_emulate.get_collection(self.collection_name).schema["fields"].get(name) is not None:
            collection = self.stack.early_op_emulate.get_collection(self.collection_name)
        else:
            collection = self.stack.late_op_emulate.get_collection(self.collection_name)
        collection.emulate_field_operator(name, operator)

    def emulate_field_filtering(self, name: str):
        collection = self.stack.late_op_emulate.get_collection(self.collection_name)
        field = collection.schema["fields"][name]

        if field["column_type"] == PrimitiveType.STRING:
            operators = MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[field["column_type"]]

            for operator in operators:
                if operator not in field.get("filter_operators", {}):
                    self.emulate_field_operator(name, operator)

    def add_many_to_one_relation(
        self, name: str, foreign_collection: str, foreign_key: str, foreign_key_target: Optional[str] = None
    ):
        self._add_relation(
            name,
            PartialManyToOne(
                type=FieldType.MANY_TO_ONE,
                foreign_collection=foreign_collection,
                foreign_key=foreign_key,
                foreign_key_target=foreign_key_target,
            ),
        )

    def add_one_to_many_relation(
        self, name: str, foreign_collection: str, origin_key: str, origin_key_target: Optional[str] = None
    ):
        self._add_relation(
            name,
            PartialOneToMany(
                type=FieldType.ONE_TO_MANY,
                foreign_collection=foreign_collection,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
            ),
        )

    def add_one_to_one_relation(
        self, name: str, foreign_collection: str, origin_key: str, origin_key_target: Optional[str] = None
    ):
        self._add_relation(
            name,
            PartialOneToOne(
                type=FieldType.ONE_TO_ONE,
                foreign_collection=foreign_collection,
                origin_key=origin_key,
                origin_key_target=origin_key_target,
            ),
        )

    def add_many_to_many_relation(
        self,
        name: str,
        foreign_collection: str,
        through_collection: str,
        origin_key: str,
        foreign_key: str,
        origin_key_target: Optional[str] = None,
        foreign_key_target: Optional[str] = None,
    ):
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

    def _add_relation(self, name: str, definition: RelationDefinition):
        self.stack.relation.get_collection(self.collection_name).add_relation(name, definition)

    def add_hook(self, position: Position, type: CrudMethod, handler: HookHandler):
        self.stack.hook.get_collection(self.collection_name).add_hook(position, type, handler)

    def emulate_field_sorting(self, name: str):
        self.stack.sort_emulate.get_collection(self.collection_name).emulate_field_sorting(name)

    def replace_field_sorting(self, name: str, equivalent_sort: List[PlainSortClause]):
        self.stack.sort_emulate.get_collection(self.collection_name).replace_field_sorting(name, equivalent_sort)
