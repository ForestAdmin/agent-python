from typing import Dict, List, Optional

from asgiref.sync import sync_to_async
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_toolkit.interfaces.fields import is_polymorphic_many_to_one
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoPolymorphismUtil:
    _CONTENT_TYPE_CACHE: Optional[Dict[str, "ContentType"]] = None  # noqa:F821 # type:ignore

    @classmethod
    async def get_content_types(cls, force_refresh=False) -> Dict[str, "ContentType"]:  # noqa:F821 # type:ignore
        if cls._CONTENT_TYPE_CACHE is None or force_refresh is True:
            await cls._refresh_content_type()
        return cls._CONTENT_TYPE_CACHE  # type:ignore

    @classmethod
    async def _refresh_content_type(cls):
        from django.contrib.contenttypes.models import ContentType

        cls._CONTENT_TYPE_CACHE = {}
        qs = ContentType.objects.all()
        for ct in await sync_to_async(list)(qs):  # type: ignore
            model = ct.model_class()
            if model is not None:
                cls._CONTENT_TYPE_CACHE[model._meta.db_table] = ct

    @classmethod
    def is_polymorphism_implied(cls, projection: Projection, collection: BaseDjangoCollection) -> bool:
        pass
        for field_name, field_schema in collection.schema["fields"].items():
            if field_name in projection and is_polymorphic_many_to_one(field_schema):
                return True
        return False

    @classmethod
    async def replace_content_type_in_patch(
        cls, patch: RecordsDataAlias, collection: BaseDjangoCollection
    ) -> RecordsDataAlias:
        content_types = None
        for field_name, field_schema in collection.schema["fields"].items():
            if is_polymorphic_many_to_one(field_schema):
                if content_types is None:
                    content_types = await cls.get_content_types()
                if field_schema["foreign_key_type_field"] in patch.keys():
                    content_type_field = field_schema["foreign_key_type_field"]
                    patch[content_type_field] = content_types[patch[content_type_field]]
        return patch

    @classmethod
    async def replace_content_type_in_result(
        cls, result: List[RecordsDataAlias], projection: Projection, collection: BaseDjangoCollection
    ) -> List[RecordsDataAlias]:
        content_types = None
        if content_types is None:
            content_types = await cls.get_content_types()

        for field_name, field_schema in collection.schema["fields"].items():
            if is_polymorphic_many_to_one(field_schema):
                if content_types is None:
                    content_types = await cls.get_content_types()
                if field_schema["foreign_key_type_field"] in patch.keys():
                    content_type_field = field_schema["foreign_key_type_field"]
                    patch[content_type_field] = content_types[patch[content_type_field]]
        return patch
