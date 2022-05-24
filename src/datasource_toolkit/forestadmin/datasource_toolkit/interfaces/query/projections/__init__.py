from functools import reduce
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Union, cast

from typing_extensions import TypeGuard

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import RelationAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class ProjectionException(DatasourceToolkitException):
    pass


class Projection(list[str]):
    @property
    def columns(self) -> List[str]:
        return list(filter(lambda x: ":" not in x, self))

    @property
    def relations(self) -> Dict[str, "Projection"]:
        relations: Dict[str, Projection] = DefaultDict(Projection)
        for path in self:
            field, relation = path.split(":")
            if relation:
                relations[field] = Projection(*[*relations[field], relation])
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
        fields: List[str] = reduce(lambda x, y: [*x, *y], [*self, *projections], [])
        return Projection(*set(fields))

    def apply(self, records: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        results: List[RecordsDataAlias] = []
        for record in records:
            result = self.__reproject(record)
            if result:
                results.append(result)
        return results

    def with_pks(self, collection: Collection) -> "Projection":
        result = Projection(*self)
        for pk in SchemaUtils.get_primary_keys(collection.schema):
            if pk not in result:
                result.append(pk)

        for relation, projection in self.relations.items():
            schema = cast(RelationAlias, collection.schema["fields"][relation])
            association = collection.datasource.get_collection(schema["foreign_collection"])
            projection_with_pk: Projection = projection.with_pks(association).nest(relation)
            for field in projection_with_pk:
                if field not in result:
                    result.append(field)
        return result

    def nest(self, prefix: str) -> "Projection":
        if prefix:
            return Projection(*map(lambda path: f"{prefix}:{path}", self))
        return self

    def unnest(self) -> "Projection":
        prefix, _ = self[0].split(":")
        if not all([path.startswith(prefix) for path in self]):
            raise ProjectionException("Cannot unnest projection.")

        return Projection(*map(lambda path: path[len(prefix) + 1 :], self))

    def __reproject(self, record: Optional[RecordsDataAlias] = None) -> Optional[RecordsDataAlias]:
        result: Optional[RecordsDataAlias] = None
        if record:
            result = {}

            for column in self.columns:
                result[column] = record[column]

            for relation, projection in self.relations.items():
                result[relation] = projection.__reproject(record["relation"])

        return result


def is_projection(projection: Any) -> TypeGuard[Projection]:
    return isinstance(projection, Projection)
