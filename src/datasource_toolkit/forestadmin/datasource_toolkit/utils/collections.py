from typing import List, Optional, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, ForestException
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldAlias,
    OneToMany,
    RelationAlias,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
    is_polymorphic_one_to_one,
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
            raise CollectionUtilsException(
                f"{kind} not found {collection.name}.{field_name}. Fields are {','.join(fields.keys())}"
            )

        if not sub_path:
            return schema

        if not (is_many_to_one(schema) or is_one_to_one(schema)):
            raise CollectionUtilsException(f'Unexpected field type {schema["type"]}: {collection.name}.{field_name}')

        schema = cast(RelationAlias, schema)
        return cls.get_field_schema(collection.datasource.get_collection(schema["foreign_collection"]), sub_path)

    @staticmethod
    async def get_value(caller: User, collection: Collection, id: CompositeIdAlias, field: str) -> Union[int, str]:
        try:
            index = SchemaUtils.get_primary_keys(collection.schema).index(field)
        except ValueError:
            records = await collection.list(
                caller,
                PaginatedFilter({"condition_tree": ConditionTreeFactory.match_ids(collection.schema, [id])}),
                Projection(field),
            )
            res = records[0]["field"]
        else:
            res = id[index]

        return res

    @staticmethod
    async def list_relation(
        caller: User,
        collection: Collection,
        id: CompositeIdAlias,
        foreign_collection: Collection,
        relation_name: str,
        foreign_filter: PaginatedFilter,
        projection: Projection,
    ) -> List[RecordsDataAlias]:
        from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory

        relation = collection.schema["fields"][relation_name]

        if is_many_to_many(relation) and relation.get("foreign_relation") and foreign_filter.is_nestable:
            through = collection.datasource.get_collection(relation["through_collection"])
            records = await through.list(
                caller,
                await FilterFactory.make_through_filter(caller, collection, id, relation_name, foreign_filter),
                projection.nest(relation.get("foreign_relation")),
            )
            return [record[relation.get("foreign_relation")] for record in records]
        return await foreign_collection.list(
            caller,
            await FilterFactory.make_foreign_filter(caller, collection, id, relation, foreign_filter),
            projection,
        )

    @staticmethod
    async def aggregate_relation(
        caller: User,
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

        if is_many_to_many(relation) and relation.get("foreign_relation") and foreign_filter.is_nestable:
            through = collection.datasource.get_collection(relation["through_collection"])
            filter_ = await FilterFactory.make_through_filter(collection, id, relation_name, foreign_filter)

            nested_records = await through.aggregate(
                caller, filter_.to_base_filter(), aggregation.nest(relation["foreign_relation"]), limit
            )

            records: List[AggregateResult] = []
            for record in nested_records:
                group = {}
                for key, value in record["group"].items():
                    group[key.split(":")[1:]] = value
                records.append({"value": record["value"], "group": record["group"]})
            return records

        relation = cast(OneToMany, relation)
        filter_ = await FilterFactory.make_foreign_filter(caller, collection, id, relation, foreign_filter)
        return await foreign_collection.aggregate(caller, filter_.to_base_filter(), aggregation, limit)

    @staticmethod
    def get_inverse_relation(collection: Collection, relation_name: str) -> Optional[str]:
        relation = cast(RelationAlias, collection.get_field(relation_name))
        if is_polymorphic_many_to_one(relation):
            raise CollectionUtilsException(
                f"A polymorphic many to one ({collection.name}.{relation_name}) have many reverse relations"
            )
        foreign_collection = collection.datasource.get_collection(relation["foreign_collection"])
        inverse: Optional[str] = None
        for name, field_schema in foreign_collection.schema["fields"].items():
            if not is_relation(field_schema) or (
                not is_polymorphic_many_to_one(field_schema) and field_schema["foreign_collection"] != collection.name
            ):
                continue

            if (
                CollectionUtils.is_many_to_many_inverse(field_schema, relation)
                or CollectionUtils.is_many_to_one_inverse(field_schema, relation)
                or CollectionUtils.is_other_inverse(field_schema, relation)
                or CollectionUtils.is_polymorphic_many_to_one_inverse(field_schema, relation)
            ):
                inverse = name
        return inverse

    @staticmethod
    def is_polymorphic_many_to_one_inverse(field: RelationAlias, relation_field: RelationAlias) -> bool:
        if (
            is_polymorphic_many_to_one(field)
            and (is_polymorphic_one_to_one(relation_field) or is_polymorphic_one_to_many(relation_field))
            and field["foreign_key"] == relation_field["origin_key"]
            and field["foreign_key_type_field"] == relation_field["origin_type_field"]
            and relation_field["origin_type_value"] in field["foreign_collections"]
        ):
            return True
        return False

    @staticmethod
    def is_many_to_many_inverse(field: RelationAlias, relation_field: RelationAlias) -> bool:
        if (
            is_many_to_many(field)
            and is_many_to_many(relation_field)
            and field["origin_key"] == relation_field["foreign_key"]
            and field["through_collection"] == relation_field["through_collection"]
            and field["foreign_key"] == relation_field["origin_key"]
        ):
            return True
        return False

    @staticmethod
    def is_many_to_one_inverse(field: RelationAlias, relation_field: RelationAlias) -> bool:
        if (
            is_many_to_one(field)
            and (is_one_to_many(relation_field) or is_one_to_one(relation_field))
            and field["foreign_key"] == relation_field["origin_key"]
        ):
            return True
        return False

    @staticmethod
    def is_other_inverse(field: RelationAlias, relation_field: RelationAlias) -> bool:
        if (
            (is_one_to_many(field) or is_one_to_one(field))
            and is_many_to_one(relation_field)
            and field["origin_key"] == relation_field["foreign_key"]
        ):
            return True
        return False

    @staticmethod
    def get_through_target(collection: Collection, relation_name: str) -> Optional[str]:
        relation = collection.schema["fields"].get(relation_name)
        if not relation or not is_many_to_many(relation):
            raise ForestException("Relation must be many to many")

        through_collection = collection.datasource.get_collection(relation["through_collection"])
        for field_name, field in through_collection.schema["fields"].items():
            if (
                is_many_to_one(field)
                and field["foreign_collection"] == relation["foreign_collection"]
                and field["foreign_key"] == relation["foreign_key"]
                and field["foreign_key_target"] == relation["foreign_key_target"]
            ):
                return field_name
        return None
