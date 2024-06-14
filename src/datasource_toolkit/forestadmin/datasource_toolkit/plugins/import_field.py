from functools import partial, reduce
from typing import Dict, Optional

from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, is_column, is_many_to_one, is_one_to_one
from forestadmin.datasource_toolkit.plugins.plugin import Plugin
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from typing_extensions import NotRequired, TypedDict


class ImportFieldOption(TypedDict):
    path: str
    readonly: NotRequired[Optional[bool]]


class InternalImportFieldOption(TypedDict):
    name: str
    path: str
    readonly: NotRequired[Optional[bool]]


class ImportField(Plugin):
    async def run(
        self,
        datasource_customizer: "DatasourceCustomizer",  # noqa: F821 # type: ignore
        collection_customizer: "CollectionCustomizer",  # noqa: F821 # type: ignore
        options: InternalImportFieldOption,
    ):
        options = self._check_params(options)
        name = options["name"]

        def _reduce_fn(memo, field):
            collection = datasource_customizer.get_collection(memo["collection"])
            if field not in collection.schema["fields"]:
                raise ForestException(f"Field {field} not found in collection {collection.collection_name}")
            field_schema = collection.schema["fields"][field]

            if is_column(field_schema):
                return {"schema": field_schema}

            if is_many_to_one(field_schema) or is_one_to_one(field_schema):
                return {"collection": field_schema["foreign_collection"]}

            raise ForestException('Invalid options["path"]')

        result = reduce(_reduce_fn, options["path"].split(":"), {"collection": collection_customizer.collection_name})
        schema: FieldAlias = result["schema"]

        collection_customizer.add_field(
            name,
            ComputedDefinition(
                column_type=schema["column_type"],
                dependencies=[options["path"]],
                get_values=lambda records, ctx: [
                    RecordUtils.get_field_value(record, options["path"]) for record in records
                ],
                default_value=schema.get("default_value"),
                enum_values=schema.get("enum_values"),
            ),
        )

        self._handle_read_only(collection_customizer, name, schema, options)

        self._handle_sortable_and_operators(collection_customizer, name, schema, options)

    def _check_params(self, options: Dict):
        if options.get("name") is None or options.get("path") is None:
            raise ForestException("The options parameter must contains the following keys: 'name, path'")

        return options

    def _handle_sortable_and_operators(self, collection_customizer, name: str, schema: FieldAlias, options: Dict):
        for operator in schema["filter_operators"]:

            async def replacer(origin_operator, value, context):
                return {"field": options["path"], "operator": origin_operator, "value": value}

            collection_customizer.replace_field_operator(
                name,
                operator,
                partial(replacer, operator),
            )

        if schema.get("is_sortable"):
            collection_customizer.replace_field_sorting(name, [{"field": options["path"], "ascending": True}])

    def _handle_read_only(self, collection_customizer, name: str, schema: FieldAlias, options: Dict):
        if "readonly" not in options:
            options["readonly"] = schema.get("is_read_only", False)

        if not options["readonly"] and not schema.get("is_read_only", False):

            def _write_field_fn(value, ctx):
                path = options["path"].split(":")
                writing_path = {}
                nested_path = writing_path
                for index, current_path in enumerate(path):
                    nested_path[current_path] = value if index == len(path) - 1 else {}
                    nested_path = nested_path[current_path]
                return writing_path

            collection_customizer.replace_field_writing(name, _write_field_fn)

        if schema.get("is_read_only", False) is True and options["readonly"] is False:
            raise ForestException(
                f'Readonly option should not be false because the field "{options["path"]}" is not writable'
            )
