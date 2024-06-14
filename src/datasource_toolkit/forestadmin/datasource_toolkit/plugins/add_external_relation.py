from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType, PrimitiveTypeLiteral
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.plugins.plugin import Plugin
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function
from typing_extensions import NotRequired, TypedDict


class AddExternalRelationOptions(TypedDict):
    name: str
    schema: Dict[str, PrimitiveType]
    list_records: Callable[[RecordsDataAlias, CollectionCustomizationContext], Union[Awaitable[Any], Any]]
    dependencies: NotRequired[Optional[List[str]]]


class ExternalRelationDefinition(TypedDict):
    schema: Dict[str, Union[PrimitiveType, PrimitiveTypeLiteral]]
    list_records: Callable[[RecordsDataAlias, CollectionCustomizationContext], Union[Awaitable[Any], Any]]
    dependencies: NotRequired[Optional[List[str]]]


class AddExternalRelation(Plugin):
    async def run(
        self,
        datasource_customizer: "DatasourceCustomizer",  # noqa: F821 # type:ignore
        collection_customizer: "CollectionCustomizer",  # noqa: F821 # type:ignore
        options: AddExternalRelationOptions,
    ):
        primary_keys = SchemaUtils.get_primary_keys(collection_customizer.schema)

        if "name" not in options or "schema" not in options or "list_records" not in options:  # type: ignore
            raise ForestException(
                "The options parameter must contains the following keys: 'name, schema, list_records'"
            )

        async def get_values_fn(records, context):
            ret = []
            for record in records:
                value = await call_user_function(options["list_records"], record, context)
                ret.append(value)
            return ret

        collection_customizer.add_field(
            options["name"],
            ComputedDefinition(
                column_type=[options["schema"]],  # type:ignore
                dependencies=options.get("dependencies", primary_keys),  # type:ignore
                get_values=get_values_fn,
            ),
        )
