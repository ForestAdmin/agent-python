from typing import Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, RelationAlias, is_many_to_one, is_one_to_one
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection as CollectionModel
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
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
