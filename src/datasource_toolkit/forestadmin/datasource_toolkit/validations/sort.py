from typing import List

from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class SortValidator:
    @staticmethod
    def validate(collection: Collection, sorts: List[PlainSortClause]):
        for sort in sorts:
            FieldValidator.validate(collection, sort["field"])
