from typing import List, Optional, Union, cast

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldAlias,
    ManyToMany,
    OneToMany,
    RelationAlias,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_relation,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection as CollectionModel
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class CollectionUtilsException(DatasourceToolkitException):
    pass


class CollectionUtils:
    @classmethod
    def get_field_schema(cls, collection: CollectionModel, path: str) -> FieldAlias:
        fields = collection.schema["fields"]
        field_name = path
        sub_path = None
        splited = path.split(":")
        if len(splited) > 1:
            field_name = splited[0]
            sub_path = ":".join(splited[1:])
        try:
            schema = fields[field_name]
        except KeyError:
            kind = "Relation" if sub_path else "Column"
            raise CollectionUtilsException(f"{kind} not found {collection.name}.{field_name}")

        if not sub_path:
            return schema

        if not (is_many_to_one(schema) or is_one_to_one(schema)):
            raise CollectionUtilsException(f'Unexpected field type {schema["type"]}: {collection.name}.{field_name}')

        schema = cast(RelationAlias, schema)
        return cls.get_field_schema(collection.datasource.get_collection(schema["foreign_collection"]), sub_path)

    @staticmethod
    async def get_value(collection: Collection, id: CompositeIdAlias, field: str) -> Union[int, str]:
        try:
            index = SchemaUtils.get_primary_keys(collection.schema).index(field)
        except ValueError:
            records = await collection.list(
                PaginatedFilter({"condition_tree": ConditionTreeFactory.match_ids(collection.schema, [id])}),
                Projection(field),
            )
            res = records[0]["field"]
        else:
            res = id[index]

        return res

    @staticmethod
    async def list_relation(
        collection: Collection,
        id: CompositeIdAlias,
        foreign_collection: Collection,
        relation: Union[ManyToMany, OneToMany],
        foreign_filter: PaginatedFilter,
        projection: Projection,
    ) -> List[RecordsDataAlias]:
        from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory

        if is_many_to_many(relation) and relation["foreign_relation"] and foreign_filter.is_nestable:
            through = collection.datasource.get_collection(relation["through_collection"])
            records = await through.list(
                await FilterFactory.make_through_filter(collection, id, relation, foreign_filter),
                projection.nest(relation["foreign_relation"]),
            )
            return [record[relation["foreign_relation"]] for record in records]
        return await foreign_collection.list(
            await FilterFactory.make_foreign_filter(collection, id, relation, foreign_filter), projection
        )

    @staticmethod
    async def aggregate_relation(
        collection: Collection,
        id: CompositeIdAlias,
        relation_name: str,
        foreign_filter: Filter,
        aggregation: Aggregation,
        limit: Optional[int] = None,
    ):
        from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory

        relation = SchemaUtils.get_to_many_relation(collection.schema, relation_name)
        foreign_collection = collection.datasource.get_collection(relation["foreign_collection"])

        if is_many_to_many(relation) and relation["foreign_relation"] and foreign_filter.is_nestable:
            through = collection.datasource.get_collection(relation["through_collection"])
            filter = await FilterFactory.make_through_filter(collection, id, relation, foreign_filter)

            nested_records = await through.aggregate(
                filter.to_base_filter(), aggregation.nest(relation["foreign_relation"]), limit
            )

            records: List[AggregateResult] = []
            for record in nested_records:
                group = {}
                for key, value in record["group"].items():
                    group[key.split(":")[1:]] = value
                records.append({"value": record["value"], "group": record["group"]})
            return records

        relation = cast(OneToMany, relation)
        filter = await FilterFactory.make_foreign_filter(collection, id, relation, foreign_filter)
        return await foreign_collection.aggregate(filter.to_base_filter(), aggregation, limit)

    @staticmethod
    def get_inverse_relation(collection: Collection, relation_name: str) -> Optional[str]:
        relation = cast(RelationAlias, collection.get_field(relation_name))
        foreign_collection = collection.datasource.get_collection(relation["foreign_collection"])
        inverse: Optional[str] = None
        for name, field_schema in foreign_collection.schema["fields"].items():
            is_many_to_many_inverse = (
                is_many_to_many(field_schema)
                and is_many_to_many(relation)
                and field_schema["origin_key"] == relation["foreign_key"]
                and field_schema["through_collection"] == relation["through_collection"]
                and field_schema["foreign_key"] == relation["origin_key"]
            )
            is_many_to_one_inverse = (
                is_many_to_one(field_schema)
                and (is_one_to_many(relation) or is_one_to_one(relation))
                and field_schema["foreign_key"] == relation["origin_key"]  # type: ignore
            )
            is_other_inverse = (
                (is_one_to_many(field_schema) or is_one_to_one(field_schema))
                and is_many_to_one(relation)
                and field_schema["origin_key"] == relation["foreign_key"]
            )
            if (
                is_relation(field_schema)
                and (is_many_to_many_inverse or is_many_to_one_inverse or is_other_inverse)
                and field_schema["foreign_collection"] == collection.name
            ):
                inverse = name
                break
        return inverse
