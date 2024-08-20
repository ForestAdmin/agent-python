import json
from typing import Dict, List, Optional, Union

from django.db.models import (
    DateField,
    Field,
    ForeignKey,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel,
    Model,
    OneToOneField,
    OneToOneRel,
    TimeField,
)
from django.db.models.fields import AutoFieldMixin
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_django.utils.type_converter import FilterOperator, TypeConverter
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    PolymorphicManyToOne,
    PolymorphicOneToMany,
    PolymorphicOneToOne,
    PrimitiveType,
    Validation,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from typing_extensions import TypeGuard

try:
    # GeneratedField is available since django 5
    from django.db.models import GeneratedField
except ImportError:
    GeneratedField = None


class FieldFactory:
    @staticmethod
    def _build_enum_values(field: Field) -> Optional[List[str]]:
        if field.choices:
            return [str(c[0]) for c in field.choices]  # type: ignore
        return None

    @staticmethod
    def _build_is_read_only(field: Field) -> bool:
        if field.primary_key:
            return isinstance(field, AutoFieldMixin)
        elif isinstance(field, DateField) or isinstance(field, TimeField):
            return field.auto_now is True or field.auto_now_add is True
        if GeneratedField is not None and isinstance(field, GeneratedField):
            return True
        return not field.editable

    @classmethod
    def _build_validations(cls, field: Field) -> List[Validation]:
        validations: List[Validation] = []
        if not (field.null or field.blank) and not cls._build_is_read_only(field) and not field.has_default():
            validations.append(
                {
                    "operator": Operator.PRESENT,
                }
            )
        if field.max_length:
            validations.append({"operator": Operator.SHORTER_THAN, "value": field.max_length})

        return validations

    @classmethod
    def build(cls, field: Field, current_model: Model) -> Column:
        column_type = TypeConverter.convert(field)  # type: ignore

        default_value = field.default
        try:
            # field.get_default() evaluate a function if default is a function
            # we prefer don't have a default value rather than a false one
            json.dumps(default_value)
        except TypeError:  # not JSON Serializable
            default_value = None

        # when model inheritance (https://docs.djangoproject.com/en/5.0/topics/db/models/#multi-table-inheritance),
        # you inherit from parent model attributes, and also his pk ;
        # but the pk of the parent model is not the pk of the current model!
        is_primary_key = field.primary_key and current_model == field.model

        return {
            "column_type": column_type,
            "is_primary_key": is_primary_key,  # type: ignore
            "is_read_only": cls._build_is_read_only(field),
            "default_value": default_value,
            "is_sortable": True,
            "validations": cls._build_validations(field),
            "filter_operators": FilterOperator.get_operators_for_field(field),
            "enum_values": cls._build_enum_values(field),
            "type": FieldType.COLUMN,
        }


class DjangoCollectionFactory:
    @staticmethod
    def _build_one_to_many(relation: ManyToOneRel) -> OneToMany:
        return {
            "foreign_collection": relation.target_field.model._meta.db_table,
            "origin_key": relation.field.attname,
            "origin_key_target": relation.field.target_field.attname,
            "type": FieldType.ONE_TO_MANY,
        }

    @staticmethod
    def _build_many_to_one(relation: Union[OneToOneField, ForeignKey, ManyToOneRel]) -> ManyToOne:
        if isinstance(relation, ManyToOneRel):
            foreign_key = relation.field.attname
        elif isinstance(relation, ForeignKey) or isinstance(relation, OneToOneField):
            foreign_key = relation.attname
        return {
            "foreign_collection": relation.target_field.model._meta.db_table,
            "foreign_key": foreign_key,
            "foreign_key_target": relation.target_field.attname,
            "type": FieldType.MANY_TO_ONE,
        }

    @staticmethod
    def _build_one_to_polymorphic(
        relation: "GenericRelation", model: Model  # noqa: F821  # type: ignore
    ) -> Union[PolymorphicOneToMany, PolymorphicOneToOne]:
        foreign_model = relation.target_field.model
        ret = {
            "foreign_collection": foreign_model._meta.db_table,  # app_addresses
            "origin_key": relation.object_id_field_name,  # addressable_id
            "origin_key_target": model._meta.pk.name,  # id
            "origin_type_field": relation.content_type_field_name,  # addressable_type
            "origin_type_value": model._meta.db_table,  # app_customer
        }

        for uniqueness in relation.target_field.model._meta.unique_together:
            if len(uniqueness) == 2 and ret["origin_type_field"] in uniqueness and ret["origin_key"] in uniqueness:
                ret["type"] = FieldType.POLYMORPHIC_ONE_TO_ONE
                break
        else:
            ret["type"] = FieldType.POLYMORPHIC_ONE_TO_MANY
        return ret  # type:ignore

    @staticmethod
    def _build_field_override_for_many_to_one_polymorphic(
        relation: "GenericForeignKey", model: Model, foreign_collections: List[str]  # noqa: F821  # type: ignore
    ) -> Dict[str, Dict]:
        overrides = {}
        # override fk field
        overrides[relation.fk_field] = {
            **FieldFactory.build(model._meta.get_field(relation.fk_field), model),
            "is_read_only": True,
        }
        # override ct field
        type_field = model._meta.get_field(relation.ct_field)
        overrides[relation.ct_field] = {
            "column_type": PrimitiveType.ENUM,
            "is_primary_key": type_field.primary_key,  # type: ignore
            "is_read_only": True,
            "default_value": None,
            "is_sortable": True,
            "validations": [],
            "filter_operators": FilterOperator.get_for_type(PrimitiveType.STRING),
            "enum_values": foreign_collections,
            "type": FieldType.COLUMN,
        }
        # override ct_id field
        overrides[type_field.column] = {
            **FieldFactory.build(model._meta.get_field(type_field.column), model),
            "is_read_only": True,
        }
        return overrides

    @staticmethod
    def _build_many_to_one_polymorphic(
        relation: "GenericForeignKey", model: Model  # noqa: F821  # type: ignore
    ) -> PolymorphicManyToOne:
        targets = {}
        for field in model._meta.get_fields(include_hidden=True):
            if (
                not is_generic_rel(field)
                or field.remote_field.content_type_field_name != relation.ct_field  # type:ignore
                or field.remote_field.object_id_field_name != relation.fk_field  # type:ignore
            ):
                continue
            targets[field.remote_field.model._meta.db_table] = field.remote_field.model._meta.pk.name  # type:ignore
        return {
            "foreign_collections": [*targets.keys()],
            "foreign_key": relation.fk_field,
            "foreign_key_type_field": relation.ct_field,
            "foreign_key_targets": targets,
            "type": FieldType.POLYMORPHIC_MANY_TO_ONE,
        }

    @staticmethod
    def _build_one_to_one(relation: OneToOneRel) -> OneToOne:
        return {
            "foreign_collection": relation.target_field.model._meta.db_table,
            "origin_key": relation.field.attname,
            "origin_key_target": relation.field.target_field.attname,
            "type": FieldType.ONE_TO_ONE,
        }

    @staticmethod
    def _build_many_to_many(relation: Union[ManyToManyField, ManyToManyRel]) -> ManyToMany:
        kwargs: Dict[str, str] = {"foreign_collection": relation.target_field.model._meta.db_table}

        if isinstance(relation, ManyToManyField):
            kwargs["through_collection"] = relation.remote_field.through._meta.db_table

            kwargs["origin_key"] = relation.m2m_column_name()
            kwargs["foreign_key"] = relation.m2m_reverse_name()

        elif isinstance(relation, ManyToManyRel):
            kwargs["through_collection"] = relation.through._meta.db_table

            kwargs["origin_key"] = relation.field.m2m_reverse_name()
            kwargs["foreign_key"] = relation.field.m2m_column_name()

        kwargs["origin_key_target"] = relation.model._meta.pk.attname
        kwargs["foreign_key_target"] = relation.target_field.model._meta.pk.attname

        return ManyToMany(type=FieldType.MANY_TO_MANY, foreign_relation=None, **kwargs)

    @staticmethod
    def build(model: Model, introspect_polymorphic_relations: bool) -> CollectionSchema:  # noqa:C901
        fields = {}
        overrides = {}
        for field in model._meta.get_fields(include_hidden=True):
            if not field.is_relation:
                fields[field.name] = FieldFactory.build(field, model)
            else:
                if is_generic_rel(field):
                    continue  # will be handled during is_generic_foreign_key

                # get_fields with include hidden doesn't include autogenerated foreign key fields (ending with _id)
                if isinstance(field, ForeignKey):
                    fields[field.attname] = FieldFactory.build(field, model)

                if field.one_to_one is True:
                    if isinstance(field, OneToOneField):
                        fields[field.name] = DjangoCollectionFactory._build_many_to_one(field)
                    else:
                        fields[field.name] = DjangoCollectionFactory._build_one_to_one(field)

                elif field.one_to_many is True:
                    if is_generic_relation(field):
                        if introspect_polymorphic_relations:
                            fields[field.name] = DjangoCollectionFactory._build_one_to_polymorphic(field, model)
                        else:
                            ForestLogger.log(
                                "info",
                                f"Ignoring {model._meta.db_table}.{field.name} "
                                "because polymorphic relation is not supported.",
                            )
                    else:
                        fields[f"{field.name}_{field.remote_field.name}"] = DjangoCollectionFactory._build_one_to_many(
                            field
                        )

                elif field.many_to_one is True:
                    if is_generic_foreign_key(field):
                        if introspect_polymorphic_relations:
                            fields[field.name] = DjangoCollectionFactory._build_many_to_one_polymorphic(field, model)
                            overrides.update(
                                DjangoCollectionFactory._build_field_override_for_many_to_one_polymorphic(
                                    field, model, fields[field.name]["foreign_collections"]
                                )
                            )
                        else:
                            ForestLogger.log(
                                "info",
                                f"Ignoring {model._meta.db_table}.{field.name} "
                                "because polymorphic relation is not supported.",
                            )

                    else:
                        fields[field.name] = DjangoCollectionFactory._build_many_to_one(field)

                elif field.many_to_many is True:
                    fields[field.name] = DjangoCollectionFactory._build_many_to_many(field)

        if overrides:
            fields.update(overrides)
        return {"actions": {}, "fields": fields, "searchable": False, "segments": [], "countable": True, "charts": []}


def is_generic_foreign_key(field) -> TypeGuard["GenericForeignKey"]:  # noqa: F821 # type: ignore
    """return true if it is the polymorphism relation"""
    # when imported at top level (before app.Ready):
    # it raise django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
    from django.contrib.contenttypes.fields import GenericForeignKey

    return isinstance(field, GenericForeignKey)


def is_generic_relation(field) -> TypeGuard["GenericRelation"]:  # noqa: F821 # type: ignore
    """return true if it is the reverse polymorphism relation"""
    # when imported at top level (before app.Ready):
    # it raise django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
    from django.contrib.contenttypes.fields import GenericRelation

    return isinstance(field, GenericRelation)


def is_generic_rel(field) -> TypeGuard["GenericRel"]:  # noqa: F821 # type: ignore
    """return true if it is a potential relation of the polymorphism relation"""
    # when imported at top level (before app.Ready):
    # it raise django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
    from django.contrib.contenttypes.fields import GenericRel

    return isinstance(field, GenericRel)
