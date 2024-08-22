from collections import Counter
from functools import reduce
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import RelationAlias, is_polymorphic_many_to_one
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from typing_extensions import TypeGuard


class ProjectionException(DatasourceToolkitException):
    pass


class Projection(list):  # type: ignore
    def __init__(self, *items: Any):
        super(Projection, self).__init__(items)  # type: ignore

    @property
    def columns(self) -> List[str]:
        return list(filter(lambda x: ":" not in x, self))

    def __eq__(self, other: "Projection") -> bool:
        return set(self) == set(other)

    @property
    def relations(self: List[str]) -> Dict[str, "Projection"]:
        relations: Dict[str, Projection] = DefaultDict(Projection)
        for path in self:
            splited = path.split(":")
            field = splited[0]
            if len(splited) > 1:
                relation = splited[1:]
                relations[field] = Projection(*relations[field], ":".join(relation))
        return relations

    def replace(self, handler: Callable[[str], Union["Projection", str, List[str]]]) -> "Projection":
        def reducer(memo: Projection, paths: Union["Projection", str, List[str]]) -> Projection:
            if isinstance(paths, str):
                new_paths = [paths]
            else:
                new_paths: Union[List[str], "Projection"] = paths
            return memo.union(new_paths)

        handled = map(handler, self)

        return reduce(reducer, handled, Projection())

    def union(self, *projections: Union["Projection", List[str]]) -> "Projection":
        fields: List[str] = reduce(lambda x, y: [*x, *y], [self, *projections], [])  # type: ignore
        return Projection(*Counter(fields))

    def apply(self, records: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        results: List[RecordsDataAlias] = []
        for record in records:
            result = self._reproject(record)
            if result:
                results.append(result)
        return results

    def with_pks(self, collection: Collection) -> "Projection":
        result = Projection(*self)
        for pk in SchemaUtils.get_primary_keys(collection.schema):
            if pk not in result:
                result.append(pk)  # type: ignore

        for relation, projection in self.relations.items():
            if is_polymorphic_many_to_one(collection.schema["fields"][relation]):
                continue
            schema = cast(RelationAlias, collection.schema["fields"][relation])
            association = collection.datasource.get_collection(schema["foreign_collection"])
            projection_with_pk: Projection = projection.with_pks(association).nest(relation)
            for field in projection_with_pk:  # type: ignore
                if field not in result:
                    result.append(field)  # type: ignore
        return result

    def nest(self, prefix: Optional[str]) -> "Projection":
        if prefix:
            return Projection(*map(lambda path: f"{prefix}:{path}", self))  # type: ignore
        return self

    def unnest(self) -> "Projection":
        splitted = self[0].split(":")  # type: ignore
        prefix = splitted[0]  # type: ignore
        if not all([path.startswith(prefix) for path in self]):  # type: ignore
            raise ProjectionException("Cannot unnest projection.")

        return Projection(*map(lambda path: path[len(prefix) + 1 :], self))  # type: ignore

    def _reproject(self, record: Optional[RecordsDataAlias] = None) -> Optional[RecordsDataAlias]:
        result: Optional[RecordsDataAlias] = None
        if record:
            result = {}

            for column in self.columns:
                try:
                    result[column] = record[column]
                except KeyError:
                    raise ProjectionException(f"the column ‘{column}‘ is missing in your record")

            for relation, projection in self.relations.items():
                result[relation] = projection._reproject(record.get(relation))

        return result


def is_projection(projection: Any) -> TypeGuard[Projection]:
    return isinstance(projection, Projection)
