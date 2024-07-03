from typing import Any, cast

from forestadmin.datasource_toolkit.interfaces.fields import RelationAlias
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


def rewrite_fields(collection: Any, path: str) -> Projection:
    if ":" in path:
        prefix = path.split(":")[0]
        schema = cast(RelationAlias, collection.get_field(prefix))
        association = collection.datasource.get_collection(schema["foreign_collection"])
        return Projection(path).unnest().replace(lambda sub_path: rewrite_fields(association, sub_path)).nest(prefix)

    computed = collection.get_computed(path)
    if computed is None:
        return Projection(path)
    else:
        return Projection(*computed["dependencies"]).replace(lambda dep_path: rewrite_fields(collection, dep_path))
