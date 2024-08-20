from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

from django.db.models import Model
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_django.utils.polymorphic_util import DjangoPolymorphismUtil
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    PrimitiveType,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_one,
)
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
            record_data[field_name] = serialize_value(
                getattr(instance, field_name), cast(Column, collection.schema["fields"][field_name])
            )

    for relation_name, subfields in projection.relations.items():
        relation = getattr(instance, relation_name, None)
        if relation is None:
            record_data[relation_name] = None
            continue

        relation_schema = collection.schema["fields"][relation_name]
        _projection = subfields
        foreign_collection_name = relation_schema.get("foreign_collection")

        if is_polymorphic_one_to_one(relation_schema):
            relation = relation.all()  #  type:ignore
            # when using relation.first, django make a request for ordering, so we avoid this extra request by using all
            if not relation.exists():
                record_data[relation_name] = None
                continue
            relation = relation[0]

        elif is_polymorphic_many_to_one(relation_schema):
            target_type = getattr(instance, relation_schema["foreign_key_type_field"], None)

            target_type = DjangoPolymorphismUtil.get_collection_name_from_content_type(target_type)
            foreign_collection = collection.datasource.get_collection(target_type)
            _projection = ProjectionFactory.all(foreign_collection, allow_nested=False)
            foreign_collection_name = foreign_collection.name

        foreign_collection = collection.datasource.get_collection(foreign_collection_name)  # type:ignore
        record_data[relation_name] = instance_to_record_data(
            relation,
            _projection,
            foreign_collection,
        )
    return record_data


def serialize_value(value: Any, column_schema: Column):
    if value is None:
        return value
    if column_schema["column_type"] == PrimitiveType.NUMBER:
        if isinstance(value, Decimal):
            return float(value)
        else:
            return value

    # Do we want to return date and datetime as object or isoformat ??
    elif column_schema["column_type"] == PrimitiveType.DATE_ONLY:
        return value if isinstance(value, date) else date.fromisoformat(value)
    elif column_schema["column_type"] == PrimitiveType.DATE:
        return value if isinstance(value, datetime) else datetime.fromisoformat(value)

    return value
