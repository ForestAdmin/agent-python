import asyncio
import logging
import tempfile
from unittest import TestCase
from unittest.mock import ANY, patch

from forestadmin.agent_toolkit.utils.forest_schema.emitter import SchemaEmitter
from forestadmin.agent_toolkit.utils.forest_schema.generator_collection import SchemaCollectionGenerator
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class TestSchemaEmitter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
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
            }
        )
        cls.book_collection.add_segments([{"id": "Book.unsold", "name": "unsold books"}])
        cls.book_collection.add_action("burn", Action(generate_file=False, scope=ActionsScope.SINGLE, static_form=True))
        cls.datasource.add_collection(cls.book_collection)
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
            }
        )
        cls.datasource.add_collection(cls.author_collection)
        cls.options = {"is_production": False, "prefix": "", "schema_path": ""}
        cls.meta = {
            "liana": "agent-python",
            "liana_version": "1.4.0",
            "stack": {
                "engine": "python",
                "engine_version": "3.10.11",
            },
        }

    def test_get_serialized_schema_should_generate_in_development_environment_and_write_file(self):
        with patch(
            "forestadmin.agent_toolkit.utils.forest_schema.emitter.SchemaEmitter.generate",
            return_value="generate_return",
        ) as mock_generate:
            with patch(
                "forestadmin.agent_toolkit.utils.forest_schema.emitter.SchemaEmitter.serialize"
            ) as mock_serialize:
                with patch("forestadmin.agent_toolkit.utils.forest_schema.emitter.open") as mock_open:
                    with patch("forestadmin.agent_toolkit.utils.forest_schema.emitter.json.dump") as mock_json:
                        self.loop.run_until_complete(
                            SchemaEmitter.get_serialized_schema(
                                {**self.options, "is_production": False, "schema_path": "/tmp/schema_path.json"},
                                self.datasource,
                                self.meta,
                            )
                        )

                        mock_generate.assert_awaited_once_with("", self.datasource)
                        mock_open.assert_called_with("/tmp/schema_path.json", "w", encoding="utf-8")
                        mock_json.assert_called_with(
                            {"collections": "generate_return", "meta": self.meta}, ANY, indent=4
                        )
                        mock_serialize.assert_called_once_with("generate_return", self.meta)

    def test_get_serialized_schema_should_read_file_in_production_environment(self):
        with patch("forestadmin.agent_toolkit.utils.forest_schema.emitter.SchemaEmitter.generate") as mock_generate:
            with patch(
                "forestadmin.agent_toolkit.utils.forest_schema.emitter.SchemaEmitter.serialize"
            ) as mock_serialize:
                with patch("forestadmin.agent_toolkit.utils.forest_schema.emitter.open") as mock_open:
                    mock_open.return_value.__enter__.return_value = "open_return"
                    with patch(
                        "forestadmin.agent_toolkit.utils.forest_schema.emitter.json.load",
                        return_value={"collections": []},
                    ) as mock_json:
                        self.loop.run_until_complete(
                            SchemaEmitter.get_serialized_schema(
                                {**self.options, "is_production": True, "schema_path": "/tmp/schema_path.json"},
                                self.datasource,
                                self.meta,
                            )
                        )

                        mock_generate.assert_not_called()
                        mock_open.assert_called_with("/tmp/schema_path.json", "r", encoding="utf-8")
                        mock_json.assert_called_with("open_return")
                        mock_serialize.assert_called_once_with([], self.meta)

    def test_get_serialized_schema_should_log_if_there_is_no_schema_file(self):
        with self.assertLogs("forestadmin", logging.ERROR) as logger:
            self.assertRaisesRegex(
                FileNotFoundError,
                r"\[Errno 2\] No such file or directory: '/tmp/false_path.json'",
                self.loop.run_until_complete,
                SchemaEmitter.get_serialized_schema(
                    {**self.options, "is_production": True, "schema_path": "/tmp/false_path.json"},
                    self.datasource,
                    self.meta,
                ),
            )
            self.assertEqual(
                logger.output,
                [
                    "ERROR:forestadmin:Can't read /tmp/false_path.json. Providing a schema is mandatory in production."
                    " Skipping..."
                ],
            )

    def test_generate_should_build_all_collections_and_sort_by_name(self):
        with patch(
            "forestadmin.agent_toolkit.utils.forest_schema.emitter.SchemaCollectionGenerator.build",
            wraps=SchemaCollectionGenerator.build,
        ) as spy_build:
            collections_schema = self.loop.run_until_complete(SchemaEmitter.generate("", self.datasource))
            spy_build.assert_any_await("", self.author_collection)
            spy_build.assert_any_await("", self.book_collection)

        self.assertEqual(collections_schema[0]["name"], "Author")
        self.assertEqual(collections_schema[1]["name"], "Book")

    def test_serialized_should_correctly_serialized_collection(self):
        collections = self.loop.run_until_complete(SchemaEmitter.generate("", self.datasource))

        serialized_collections = SchemaEmitter.serialize([collections[0]], self.meta)

        self.assertEqual(
            serialized_collections["meta"],
            {**self.meta, "schemaFileHash": "485fe9769d94329de2ac09866f0135131c0148a5"},
        )
        self.assertEqual(serialized_collections["included"], [])
        self.assertEqual(
            serialized_collections["data"][0],
            {
                "id": "Author",
                "type": "collections",
                "attributes": {
                    "name": "Author",
                    "isReadOnly": False,
                    "isSearchable": False,
                    "paginationType": "page",
                    "fields": [
                        {
                            "defaultValue": None,
                            "enums": None,
                            "field": "name",
                            "inverseOf": None,
                            "isFilterable": True,
                            "isPrimaryKey": False,
                            "isReadOnly": False,
                            "isRequired": False,
                            "isSortable": True,
                            "reference": None,
                            "type": "String",
                            "validations": [],
                        },
                        {
                            "defaultValue": None,
                            "enums": None,
                            "field": "primary_id",
                            "inverseOf": None,
                            "isFilterable": True,
                            "isPrimaryKey": True,
                            "isReadOnly": True,
                            "isRequired": False,
                            "isSortable": True,
                            "reference": None,
                            "type": "Uuid",
                            "validations": [],
                        },
                    ],
                },
                "relationships": {"actions": {"data": []}, "segments": {"data": []}},
            },
        )

    def test_serialized_should_correctly_serialized_actions_and_segments(self):
        collections = self.loop.run_until_complete(SchemaEmitter.generate("", self.datasource))

        with patch(
            "forestadmin.agent_toolkit.utils.forest_schema.emitter.SchemaEmitter.get_serialized_collection_relation",
            wraps=SchemaEmitter.get_serialized_collection_relation,
        ) as spy_serialize_collection_relation:
            SchemaEmitter.serialize([collections[1]], self.meta)
            spy_serialize_collection_relation.assert_any_call(collections[1], "segments")
            spy_serialize_collection_relation.assert_any_call(collections[1], "actions")

    def test_should_update_schema_file_hash_if_only_agent_version_changed(self):
        file_name = tempfile.NamedTemporaryFile().name
        schema = self.loop.run_until_complete(
            SchemaEmitter.get_serialized_schema(
                {**self.options, "is_production": False, "schema_path": file_name},
                self.datasource,
                {**self.meta, "liana_version": "1.4.0"},
            )
        )
        first_hash = schema["meta"]["schemaFileHash"]

        schema = self.loop.run_until_complete(
            SchemaEmitter.get_serialized_schema(
                {**self.options, "is_production": True, "schema_path": file_name},
                self.datasource,
                {**self.meta, "liana_version": "1.4.1"},
            )
        )
        second_hash = schema["meta"]["schemaFileHash"]
        self.assertNotEqual(first_hash, second_hash)
