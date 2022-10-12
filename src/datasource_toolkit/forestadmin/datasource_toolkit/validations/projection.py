from typing import List

from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class ProjectionValidator:
    @staticmethod
    def validate(collection: Collection, projection: List[str]) -> None:
        for field in projection:
            FieldValidator.validate(collection, field)
