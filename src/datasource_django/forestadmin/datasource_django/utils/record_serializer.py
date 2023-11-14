from django.db.models import Model
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


def instance_to_record_data(instance: Model, projection: Projection):
    record_data = {}
    for field_name in projection.columns:
        record_data[field_name] = getattr(instance, field_name)

    for relation_name, subfields in projection.relations.items():
        relation = getattr(instance, relation_name)
        record_data[relation_name] = {subfield: getattr(relation, subfield) for subfield in subfields}

    return record_data
