from typing import Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType, is_column
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidator
from forestadmin.datasource_toolkit.validations.rules import (
    MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE,
    MAP_ALLOWED_TYPES_FOR_COLUMN_TYPE,
    MAP_ALLOWED_TYPES_FOR_OPERATOR,
)
from forestadmin.datasource_toolkit.validations.type_getter import TypeGetter


class ConditionTreeValidatorException(DatasourceToolkitException):
    pass


class ConditionTreeValidator:
    @classmethod
    def _validate_leaf_condition(
        cls,
        collection: Union[
            Collection,
            "CollectionCustomizer",  # noqa:F821
        ],
    ):
        def validate_condition_tree(condition: ConditionTree):
            condition = cast(ConditionTreeLeaf, condition)
            schema = CollectionUtils.get_field_schema(collection, condition.field)
            if is_column(schema):
                cls.validate_operator(condition, schema)
                cls.validate_value_for_operator(condition, schema)
                cls.validate_operator_for_column_type(condition, schema)
                cls.validate_value_for_column_type(condition, schema)
            else:
                raise ConditionTreeValidatorException("Unable to apply condition on relation field")

        return validate_condition_tree

    @classmethod
    def validate(
        cls,
        condition_tree: ConditionTree,
        collection: Union[Collection, "CollectionCustomizer"],  # noqa:F821
    ):
        condition_tree.apply(cls._validate_leaf_condition(collection))

    @staticmethod
    def validate_operator(condition_tree: ConditionTreeLeaf, column_schema: Column):
        operators = column_schema["filter_operators"]
        error_msg = f"The given operator {condition_tree.operator} is not supported by the column:"
        if not operators:
            raise ConditionTreeValidatorException(f'{error_msg} "The column is not filterable"')
        elif condition_tree.operator not in operators:
            raise ConditionTreeValidatorException(
                f'{error_msg} "The allowed types are {[operator for operator in operators]}"'
            )

    @staticmethod
    def validate_operator_for_column_type(condition_tree: ConditionTreeLeaf, column_schema: Column):
        allowed_operators = []
        if isinstance(column_schema["column_type"], PrimitiveType):
            allowed_operators = MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE.get(column_schema["column_type"], [])
        if condition_tree.operator not in allowed_operators:
            raise ConditionTreeValidatorException(
                f"The given operator {condition_tree.operator} is not allowed with the "
                'column_type schema {column_schema["column_type"]}. \n The allowed types are: [{allowed_operators}]'
            )

    @staticmethod
    def validate_value_for_operator(condition_tree: ConditionTreeLeaf, column_schema: Column):
        value = condition_tree.value
        value_type = None
        if isinstance(column_schema["column_type"], PrimitiveType):
            value_type = TypeGetter.get(value, column_schema["column_type"])

        error_msg = (
            f'The given value attribute "{value}" (type: {value_type}) has an unexpected value '
            f'for the given operator "{condition_tree.operator}."'
        )
        allowed_types = MAP_ALLOWED_TYPES_FOR_OPERATOR.get(condition_tree.operator, [])
        if not allowed_types:
            raise ConditionTreeValidatorException(f"{error_msg} The value attribute must be empty.")

        if value_type not in allowed_types:
            raise ConditionTreeValidatorException(
                f"{error_msg} The allowed types of the field value are: [${allowed_types}]."
            )

    @staticmethod
    def validate_value_for_column_type(condition_tree: ConditionTreeLeaf, column_schema: Column):
        value = condition_tree.value
        field = condition_tree.field

        column_type = column_schema["column_type"]
        allowed_types = []
        if isinstance(column_type, PrimitiveType):
            allowed_types = MAP_ALLOWED_TYPES_FOR_COLUMN_TYPE.get(column_type, [])

        FieldValidator.validate_value(field, column_schema, value, allowed_types)
