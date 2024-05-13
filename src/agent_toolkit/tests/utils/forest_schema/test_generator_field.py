from unittest import TestCase

from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class TestGeneratorField(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.book_collection = Collection("Book", cls.datasource)
        cls.book_collection.add_fields(
            {
                "primary_id": {
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.UUID,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.UUID]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": None,
                    "is_sortable": True,
                    "is_read_only": True,
                },
                "name": {
                    "type": FieldType.COLUMN,
                    "is_primary_key": False,
                    "column_type": PrimitiveType.STRING,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.STRING]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": None,
                    "is_sortable": True,
                    "is_read_only": False,
                },
                "author_id": {
                    "type": FieldType.COLUMN,
                    "is_primary_key": False,
                    "column_type": PrimitiveType.UUID,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.UUID]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": None,
                    "is_sortable": True,
                    "is_read_only": False,
                },
                "author": {
                    "type": FieldType.MANY_TO_ONE,
                    "foreign_collection": "Author",
                    "foreign_key": "author_id",
                    "foreign_key_target": "primary_id",
                },
                "state": {
                    "type": FieldType.COLUMN,
                    "is_primary_key": False,
                    "column_type": PrimitiveType.STRING,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.STRING]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": ["PUBLISH", "CANCELED", "CENSURED"],
                    "is_sortable": True,
                    "is_read_only": False,
                },
            }
        )

    def test_should_sort_enum_values(self):
        schema_field = SchemaFieldGenerator.build(self.book_collection, "state")

        self.assertEqual(schema_field["enums"], ["CANCELED", "CENSURED", "PUBLISH"])
