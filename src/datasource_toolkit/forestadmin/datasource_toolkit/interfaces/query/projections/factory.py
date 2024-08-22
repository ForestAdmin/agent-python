from typing import List

from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    is_column,
    is_many_to_one,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class ProjectionFactory:
    @classmethod
    def all(cls, collection: Collection, prefix: str = "", allow_nested: bool = True) -> Projection:
        res: List[str] = []
        for column_name, schema in collection.schema["fields"].items():
            if is_column(schema):
                res.append(f"{prefix}{column_name}")
            elif allow_nested and (
                is_one_to_one(schema) or is_many_to_one(schema) or is_polymorphic_one_to_one(schema)
            ):
                relation = collection.datasource.get_collection(schema["foreign_collection"])
                res.extend(cls.all(relation, f"{column_name}:", False))
            elif allow_nested and is_polymorphic_many_to_one(schema):
                res.append(f"{column_name}:*")
        return Projection(*res)
