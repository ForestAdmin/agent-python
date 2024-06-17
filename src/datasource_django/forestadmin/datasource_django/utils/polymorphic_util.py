from typing import Dict, List, Optional

from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_toolkit.interfaces.fields import is_polymorphic_many_to_one
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoPolymorphismUtil:
    _CONTENT_TYPE_CACHE: Optional[Dict[str, "ContentType"]] = None  # noqa:F821 # type:ignore

    @classmethod
    def _get_content_types(cls) -> Dict[str, "ContentType"]:  # noqa:F821 # type:ignore
        return cls._CONTENT_TYPE_CACHE  # type:ignore

    @classmethod
    def request_content_type(cls):
        if cls._CONTENT_TYPE_CACHE is not None:
            return
        from django.contrib.contenttypes.models import ContentType

        cls._CONTENT_TYPE_CACHE = {}
        qs = ContentType.objects.all()
        for ct in qs:  # type: ignore
            model = ct.model_class()
            if model is not None:
                cls._CONTENT_TYPE_CACHE[model._meta.db_table] = ct

    @classmethod
    def get_polymorphism_relations(cls, projection: Projection, collection: BaseDjangoCollection) -> List[str]:
        ret = []
        for field_name, field_schema in collection.schema["fields"].items():
            if (f"{field_name}:" in projection or field_name in projection) and is_polymorphic_many_to_one(
                field_schema
            ):
                ret.append(field_name)
        return ret

    @classmethod
    def is_polymorphism_implied(cls, projection: Projection, collection: BaseDjangoCollection) -> bool:
        for field_name, field_schema in collection.schema["fields"].items():
            if f"{field_name}:" in projection and is_polymorphic_many_to_one(field_schema):
                return True
        return False

    @classmethod
    def is_type_field_of_generic_fk(cls, field_name: str, collection: BaseDjangoCollection) -> bool:
        poly_fields = cls.get_polymorphism_relations(Projection(*collection.schema["fields"].keys()), collection)
        for poly_field in poly_fields:
            schema = collection.schema["fields"][poly_field]
            if field_name == schema["foreign_key_type_field"]:
                return True
        return False

    @classmethod
    def replace_content_type_in_patch(
        cls, patch: RecordsDataAlias, collection: BaseDjangoCollection
    ) -> RecordsDataAlias:
        content_types = None
        for field_name, field_schema in collection.schema["fields"].items():
            if is_polymorphic_many_to_one(field_schema):
                if content_types is None:
                    content_types = cls._get_content_types()
                if field_schema["foreign_key_type_field"] in patch.keys():
                    content_type_field = field_schema["foreign_key_type_field"]
                    patch[content_type_field] = content_types[patch[content_type_field]]
        return patch

    # @classmethod
    # def replace_content_type_in_result(
    #     cls, result: List[RecordsDataAlias], projection: Projection, collection: BaseDjangoCollection
    # ) -> List[RecordsDataAlias]:
    #     content_types = None
    #     if content_types is None:
    #         content_types = cls._get_content_types()
    #         reversed_content_type_map = {ct.id: collection_name for collection_name, ct in content_types.items()}

    #     poly_fields = [f for f in projection if f[-1] == ":"]

    #     for row in result:
    #         for poly_field in poly_fields:
    #             field_name = poly_field[:-1]
    #             content_type_field = collection.schema["fields"][field_name]["foreign_key_type_field"]

    #             if getattr(row, content_type_field, None) is not None:
    #                 setattr(row, content_type_field, reversed_content_type_map[getattr(row, content_type_field).id])
    #     return result

    @classmethod
    def get_collection_name_from_content_type(cls, content_type) -> Optional[str]:
        if content_type is None:
            return None

        content_types = cls._get_content_types()
        for collection_name, ct in content_types.items():
            if ct.id == content_type.id:
                return collection_name
