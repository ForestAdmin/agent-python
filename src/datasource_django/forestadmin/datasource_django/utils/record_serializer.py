from django.db.models import Model
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def instance_to_record_data(instance: Model, projection: Projection) -> RecordsDataAlias:
    record_data = {}
    for field_name in projection.columns:
        record_data[field_name] = getattr(instance, field_name)

    for relation_name, subfields in projection.relations.items():
        relation = getattr(instance, relation_name, None)
        if relation:
            record_data[relation_name] = instance_to_record_data(relation, subfields)
        else:
            record_data[relation_name] = None

    return record_data
