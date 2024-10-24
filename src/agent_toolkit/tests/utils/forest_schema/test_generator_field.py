from unittest import TestCase

from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldType,
    Operator,
    PolymorphicManyToOne,
    PolymorphicOneToMany,
    PolymorphicOneToOne,
    PrimitiveType,
)
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
                "computed_filterable": {
                    "type": FieldType.COLUMN,
                    "is_primary_key": False,
                    "column_type": PrimitiveType.STRING,
                    "filter_operators": set([Operator.EQUAL]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": None,
                    "is_sortable": True,
                    "is_read_only": False,
                },
                "computed_unfilterable": {
                    "type": FieldType.COLUMN,
                    "is_primary_key": False,
                    "column_type": PrimitiveType.STRING,
                    "filter_operators": set(),
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
                    "default_value": "c24303f2-ff83-4dc2-ae7b-4f7a8ee62f2b",
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
                "tags": PolymorphicOneToMany(
                    foreign_collection="Tag",
                    origin_key="taggable_id",
                    origin_key_target="primary_id",
                    origin_type_field="taggable_type",
                    origin_type_value="Book",
                    type=FieldType.POLYMORPHIC_ONE_TO_MANY,
                ),
            }
        )

        cls.author_collection = Collection("Author", cls.datasource)
        cls.author_collection.add_fields(
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
                "tags": PolymorphicOneToOne(
                    foreign_collection="Tag",
                    origin_key="taggable_id",
                    origin_key_target="primary_id",
                    origin_type_field="taggable_type",
                    origin_type_value="Author",
                    type=FieldType.POLYMORPHIC_ONE_TO_ONE,
                ),
            }
        )

        cls.tag_collection = Collection("Tag", cls.datasource)
        cls.tag_collection.add_fields(
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
                "tag": {
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.STRING,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.STRING]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": None,
                    "is_sortable": True,
                    "is_read_only": False,
                    "is_primary_key": False,
                },
                "taggable_id": {
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.UUID,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.UUID]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": None,
                    "is_sortable": True,
                    "is_read_only": False,
                },
                "taggable_type": {
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.STRING,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.STRING]),
                    "validations": [],
                    "default_value": None,
                    "enum_values": ["Book", "Author"],
                    "is_sortable": True,
                    "is_read_only": False,
                },
                "taggable": PolymorphicManyToOne(
                    **{
                        "is_primary_key": False,
                        "type": FieldType.POLYMORPHIC_MANY_TO_ONE,
                        "foreign_collections": ["Book", "Author"],
                        "foreign_key": "taggable_id",
                        "foreign_key_type_field": "taggable_type",
                        "foreign_key_targets": {"Book": "primary_id", "Author": "primary_id"},
                    }
                ),
            }
        )

        cls.datasource.add_collection(cls.book_collection)
        cls.datasource.add_collection(cls.author_collection)
        cls.datasource.add_collection(cls.tag_collection)

    def test_should_sort_enum_values(self):
        schema_field = SchemaFieldGenerator.build(self.book_collection, "state")

        self.assertEqual(schema_field["enums"], ["CANCELED", "CENSURED", "PUBLISH"])

    def test_relations_should_not_have_default_values(self):
        schema_field = SchemaFieldGenerator.build(self.book_collection, "author")
        self.assertIsNone(schema_field["defaultValue"])

    def test_should_correctly_handle_polymorphic_types(self):
        # ManyToOne
        tag_taggable_field = SchemaFieldGenerator.build(self.tag_collection, "taggable")
        self.assertEqual(tag_taggable_field["relationship"], "BelongsTo")
        self.assertEqual(tag_taggable_field["reference"], "taggable.id")
        self.assertEqual(tag_taggable_field["inverseOf"], "Tag")
        self.assertEqual(tag_taggable_field["isSortable"], False)
        self.assertEqual(tag_taggable_field["polymorphic_referenced_models"], ["Book", "Author"])

        # oneToMany
        book_tags_field = SchemaFieldGenerator.build(self.book_collection, "tags")
        self.assertEqual(book_tags_field["relationship"], "HasMany")
        self.assertEqual(book_tags_field["reference"], "Tag.primary_id")
        self.assertEqual(book_tags_field["inverseOf"], "taggable")

        # OneToOne
        author_tags_field = SchemaFieldGenerator.build(self.author_collection, "tags")
        self.assertEqual(author_tags_field["relationship"], "HasOne")
        self.assertEqual(author_tags_field["reference"], "Tag.taggable_id")
        self.assertEqual(author_tags_field["inverseOf"], "taggable")

    def test_should_be_filterable_if_there_is_one_operator_or_more(self):
        schema_field = SchemaFieldGenerator.build(self.book_collection, "computed_filterable")
        self.assertTrue(schema_field["isFilterable"])

        schema_field = SchemaFieldGenerator.build(self.book_collection, "name")
        self.assertTrue(schema_field["isFilterable"])

    def test_should_not_be_filterable_if_there_is_zero_operator(self):
        schema_field = SchemaFieldGenerator.build(self.book_collection, "computed_unfilterable")
        self.assertFalse(schema_field["isFilterable"])
