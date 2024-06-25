from typing import Dict, List, Optional, cast

from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_toolkit.interfaces.fields import (
    PolymorphicManyToOne,
    is_polymorphic_many_to_one,
    is_reverse_polymorphic_relation,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoPolymorphismUtil:
    _CONTENT_TYPE_CACHE: Optional[Dict[str, "ContentType"]] = None  # noqa:F821 # type:ignore

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
        fields_schema = collection.schema["fields"]
        for field in projection:
            if field[-1] == ":" and is_polymorphic_many_to_one(fields_schema[field[:-1]]):
                return True
            elif ":" not in field and is_reverse_polymorphic_relation(fields_schema[field]):
                return True
            elif ":" in field:
                foreign_collection = collection.datasource.get_collection(
                    fields_schema[field.split(":")[0]]["foreign_collection"]  # type:ignore
                )
                if cls.is_polymorphism_implied(Projection(field.split(":", 1)[1]), foreign_collection):
                    return True
        return False

    @classmethod
    def is_type_field_of_generic_fk(cls, field_name: str, collection: BaseDjangoCollection) -> bool:
        generic_fk_fields = cls.get_polymorphism_relations(Projection(*collection.schema["fields"].keys()), collection)
        for poly_field in generic_fk_fields:
            schema = cast(PolymorphicManyToOne, collection.schema["fields"][poly_field])
            if field_name == schema["foreign_key_type_field"]:
                return True
        return False

    @classmethod
    def replace_content_type_in_patch(
        cls, patch: RecordsDataAlias, collection: BaseDjangoCollection
    ) -> RecordsDataAlias:
        for field_name, field_schema in collection.schema["fields"].items():
            if is_polymorphic_many_to_one(field_schema):
                if field_schema["foreign_key_type_field"] in patch.keys():
                    content_type_field = field_schema["foreign_key_type_field"]
                    patch[content_type_field] = cls._CONTENT_TYPE_CACHE.get(patch[content_type_field])
        return patch

    @classmethod
    def replace_content_type_in_condition_tree(
        cls, condition_tree: Optional[ConditionTree], collection: BaseDjangoCollection
    ) -> Optional[ConditionTree]:
        if condition_tree is None:
            return condition_tree

        if isinstance(condition_tree, ConditionTreeBranch):
            return ConditionTreeBranch(
                condition_tree.aggregator,
                [
                    cls.replace_content_type_in_condition_tree(ct, collection) for ct in condition_tree.conditions
                ],  # type:ignore
            )

        condition_tree = cast(ConditionTreeLeaf, condition_tree)
        if ":" in condition_tree.field:
            relation = condition_tree.field.split(":")[0]
            return cls.replace_content_type_in_condition_tree(
                condition_tree.unnest(),
                collection.datasource.get_collection(
                    collection.schema["fields"][relation]["foreign_collection"]  #  type:ignore
                ),
            ).nest(relation)

        if cls.is_type_field_of_generic_fk(condition_tree.field, collection):
            return ConditionTreeLeaf(
                condition_tree.field,
                condition_tree.operator,
                cls._CONTENT_TYPE_CACHE[condition_tree.value],  # type:ignore
            )
        return condition_tree

    @classmethod
    def get_collection_name_from_content_type(cls, content_type) -> Optional[str]:
        if content_type is None:
            return None

        for collection_name, ct in cls._CONTENT_TYPE_CACHE.items():
            if ct.id == content_type.id:
                return collection_name
