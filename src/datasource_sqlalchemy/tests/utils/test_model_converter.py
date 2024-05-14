import enum
from unittest import TestCase

from forestadmin.datasource_sqlalchemy.utils.model_converter import ColumnFactory
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from sqlalchemy import Column, Enum, Integer


class TestColumnFactory(TestCase):
    def test_should_introspect_fields_with_enum_values(self):
        class FieldEnum(enum.Enum):
            VALUE_ONE = "One"
            VALUE_TWO = "Two"
            VALUE_THREE = "Three"

        field = Column(Enum(FieldEnum))
        col = ColumnFactory.build(field)
        self.assertEqual(
            col,
            {
                "column_type": PrimitiveType.ENUM,
                "is_primary_key": False,
                "is_read_only": False,
                "default_value": None,
                "is_sortable": True,
                "validations": [],
                "filter_operators": {
                    Operator.NOT_IN,
                    Operator.BLANK,
                    Operator.EQUAL,
                    Operator.PRESENT,
                    Operator.MISSING,
                    Operator.IN,
                    Operator.NOT_EQUAL,
                },
                "enum_values": ["VALUE_ONE", "VALUE_TWO", "VALUE_THREE"],
                "type": FieldType.COLUMN,
            },
        )

    def test_should_correctly_introspect_pk(self):
        field = Column(Integer, primary_key=True)
        col = ColumnFactory.build(field)
        self.assertEqual(col["is_primary_key"], True)

        field = Column(Integer)
        col = ColumnFactory.build(field)
        self.assertEqual(col["is_primary_key"], False)

    def test_should_correctly_introspect_readonly(self):
        field = Column(Integer, primary_key=True)
        col = ColumnFactory.build(field)
        self.assertEqual(col["is_read_only"], True)

        field = Column(Integer, primary_key=True, autoincrement=False)
        col = ColumnFactory.build(field)
        self.assertEqual(col["is_read_only"], False)
