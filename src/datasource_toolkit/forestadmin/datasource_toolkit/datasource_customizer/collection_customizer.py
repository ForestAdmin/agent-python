from typing import List

from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionAlias
from forestadmin.datasource_toolkit.decorators.chart.types import CollectionChartDefinition
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
from forestadmin.datasource_toolkit.decorators.operators_emulate.types import OperatorDefinition
from forestadmin.datasource_toolkit.decorators.search.collections import SearchDefinition
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentAlias
from forestadmin.datasource_toolkit.decorators.write.write_replace.types import WriteDefinition
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
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

    def add_field(self, name: str, computed: ComputedDefinition):
        self.stack.early_computed.get_collection(self.collection_name).register_computed(name, computed)
        # TODO: implement the switch after relation decorator
        # const collectionBeforeRelations = this.stack.earlyComputed.getCollection(this.name);
        # const collectionAfterRelations = this.stack.lateComputed.getCollection(this.name);
        # const canBeComputedBeforeRelations = definition.dependencies.every(field => {
        # try {
        #     return !!CollectionUtils.getFieldSchema(collectionBeforeRelations, field);
        # } catch {
        #     return false;
        #     }
        # });

        # const collection = canBeComputedBeforeRelations
        #     ? collectionBeforeRelations
        #     : collectionAfterRelations;

        # collection.registerComputed(name, definition as ComputedDefinition);

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
        # TODO: review for late or early operator
        self.stack.early_op_emulate.get_collection(self.collection_name).replace_field_operator(
            name, operator, replacer
        )

    def emulate_field_operator(self, name: str, operator: Operator):
        # TODO: review for late or early operator
        self.stack.early_op_emulate.get_collection(self.collection_name).emulate_field_operator(name, operator)

    def emulate_field_filtering(self, name: str):
        # TODO: use late operator emulate when relation decorator is implemented
        collection = self.stack.early_op_emulate.get_collection(self.collection_name)
        field = collection.schema["fields"][name]

        if field["column_type"] == PrimitiveType.STRING:
            operators = MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[field["column_type"]]

            for operator in operators:
                if operator not in field.get("filter_operators", {}):
                    self.emulate_field_operator(name, operator)
