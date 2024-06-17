from decimal import Decimal
from typing import Any

from django.db.models import Model
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_django.utils.polymorphic_util import DjangoPolymorphismUtil
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def instance_to_record_data(
    instance: Model, projection: Projection, collection: BaseDjangoCollection
) -> RecordsDataAlias:
    record_data = {}
    for field_name in projection.columns:
        if DjangoPolymorphismUtil.is_type_field_of_generic_fk(field_name, collection):
            record_data[field_name] = DjangoPolymorphismUtil.get_collection_name_from_content_type(
                getattr(instance, field_name)
            )
        else:
            record_data[field_name] = serialize_value(getattr(instance, field_name))

    for relation_name, subfields in projection.relations.items():
        relation = getattr(instance, relation_name, None)
        if relation:
            foreign_collection = collection.datasource.get_collection(
                collection.schema["fields"][relation_name]["foreign_collection"]
            )
            record_data[relation_name] = instance_to_record_data(
                relation,
                subfields,
                foreign_collection,
            )
        else:
            record_data[relation_name] = None

    poly_relations = [p for p in projection if p[-1] == ":"]
    for poly_relation in poly_relations:
        record_data[poly_relation[:-1]] = None

        target_type = record_data[collection.schema["fields"][poly_relation[:-1]]["foreign_key_type_field"]]
        if target_type is None:
            continue

        foreign_collection = collection.datasource.get_collection(target_type)
        value = getattr(instance, poly_relation[:-1], None)
        if value is not None:
            record_data[poly_relation[:-1]] = instance_to_record_data(
                value,
                ProjectionFactory.all(foreign_collection),
                foreign_collection,
            )

    return record_data


def serialize_value(value: Any):
    if isinstance(value, Decimal):
        return float(value)

    return value
