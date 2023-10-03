from typing import Awaitable, Dict, Optional

from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.plugins.plugin import Plugin
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class AddExternalRelation(Plugin):
    async def run(
        self,
        datasource_customizer: "DatasourceCustomizer",  # noqa: F821
        collection_customizer: Optional["CollectionCustomizer"] = None,  # noqa: F821
        options: Optional[Dict] = {},
    ):
        primary_keys = SchemaUtils.get_primary_keys(collection_customizer.schema)

        if "name" not in options or "schema" not in options or "list_records" not in options:
            raise ForestException(
                "The options parameter must contains the following keys: 'name, schema, list_records'"
            )

        async def get_values_fn(records, context):
            ret = []
            for record in records:
                value = options["list_records"](record, context)
                if isinstance(value, Awaitable):
                    value = await value
                ret.append(value)
            return ret

        collection_customizer.add_field(
            options["name"],
            ComputedDefinition(
                column_type=[options["schema"]],
                dependencies=options.get("dependencies", primary_keys),
                get_values=get_values_fn,
            ),
        )
