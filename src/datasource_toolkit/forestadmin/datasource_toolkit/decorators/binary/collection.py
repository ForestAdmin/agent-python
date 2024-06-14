from base64 import b64decode, b64encode
from typing import Dict, List, Literal, Optional, Union

import filetype
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.binary.utils import bytes2hex, hex2bytes
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldAlias,
    Operator,
    PrimitiveType,
    Validation,
    is_column,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class BinaryCollectionDecorator(CollectionDecorator):
    OPERATORS_WITH_VALUE_REPLACEMENT = [
        Operator.AFTER,
        Operator.BEFORE,
        Operator.CONTAINS,
        Operator.ENDS_WITH,
        Operator.EQUAL,
        Operator.GREATER_THAN,
        Operator.NOT_IN,
        Operator.LESS_THAN,
        Operator.NOT_CONTAINS,
        Operator.NOT_EQUAL,
        Operator.STARTS_WITH,
        Operator.IN,
    ]

    def __init__(self, collection: Collection, datasource: Datasource):
        super().__init__(collection, datasource)
        self._binary_fields = []
        self.__use_hex_conversion = {}

    def set_binary_mode(self, name: str, type_: Union[Literal["datauri"], Literal["hex"]]):
        FieldValidator.validate(self.child_collection, name)
        field = self.child_collection.schema["fields"][name]
        if type_ not in ["datauri", "hex"]:
            raise ForestException("Invalid binary mode")

        if is_column(field) and field["column_type"] == PrimitiveType.BINARY:
            self.__use_hex_conversion[name] = type_ == "hex"
            self.mark_schema_as_dirty()
        else:
            raise ForestException("Expected a binary field")

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        fields: Dict[str, FieldAlias] = {}
        for field_name, field_schema in sub_schema["fields"].items():
            if is_column(field_schema) and field_schema["column_type"] == PrimitiveType.BINARY:
                self._binary_fields.append(field_name)
                fields[field_name] = {
                    **field_schema,
                    "column_type": PrimitiveType.STRING,
                    "validations": self._replace_validation(field_name, field_schema),
                }
            else:
                fields[field_name] = {**field_schema}
        return {**sub_schema, "fields": fields}

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        data_with_binary = [self._convert_record(True, d) for d in data]
        records = await self.child_collection.create(caller, data_with_binary)
        return [self._convert_record(False, record) for record in records]

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        filter_ = await self._refine_filter(caller, _filter)
        records = await self.child_collection.list(caller, filter_, projection)

        return [self._convert_record(False, record) for record in records]

    async def update(self, caller: User, _filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        filter_ = await self._refine_filter(caller, _filter)
        patch_with_binary = self._convert_record(True, patch)
        await self.child_collection.update(caller, filter_, patch_with_binary)

    async def aggregate(
        self, caller: User, _filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        filter_ = await self._refine_filter(caller, _filter)
        rows = await self.child_collection.aggregate(caller, filter_, aggregation, limit)

        return [
            {"value": row["value"], "group": {k: self._convert_value(False, k, v) for k, v in row["group"].items()}}
            for row in rows
        ]

    async def _refine_filter(
        self, caller: User, _filter: Optional[Union[Filter, PaginatedFilter]]
    ) -> Optional[Union[Filter, PaginatedFilter]]:
        if not _filter:
            return None

        if not _filter.condition_tree:
            return _filter

        return _filter.override({"condition_tree": _filter.condition_tree.replace(self._convert_condition_tree_leaf)})

    def _convert_condition_tree_leaf(self, leaf: ConditionTreeLeaf):
        prefix = leaf.field.split(":")[0]
        suffix = leaf.field.split(":", 1)[1] if ":" in leaf.field else None
        schema = self.child_collection.schema["fields"][prefix]

        if not is_column(schema):
            condition_tree: ConditionTree = self.datasource.get_collection(
                schema["foreign_collection"]
            )._convert_condition_tree_leaf(leaf.override({"field": suffix}))
            return condition_tree.nest(prefix)

        if leaf.operator in BinaryCollectionDecorator.OPERATORS_WITH_VALUE_REPLACEMENT:
            use_hex = self._should_use_hex(prefix)
            return leaf.override({"value": self._convert_value_helper(True, prefix, use_hex, leaf.value)})
        return leaf

    def _should_use_hex(self, name: str) -> bool:
        if name in self.__use_hex_conversion.keys():
            return self.__use_hex_conversion[name]
        return SchemaUtils.is_primary_key(self.child_collection.schema, name) or SchemaUtils.is_foreign_key(
            self.child_collection.schema, name
        )

    def _convert_record(self, to_backend: bool, record: Optional[RecordsDataAlias]) -> RecordsDataAlias:
        if record:
            return {path: self._convert_value(to_backend, path, value) for path, value in record.items()}

        return record

    def _convert_value(self, to_backend: bool, field_name: str, value):
        prefix = field_name.split(":")[0]
        suffix = field_name.split(":", 1)[1] if ":" in field_name else None
        schema = self.child_collection.schema["fields"][prefix]

        if not is_column(schema):
            foreign_collection = self.datasource.get_collection(schema["foreign_collection"])
            return (
                foreign_collection._convert_value(to_backend, suffix, value)
                if suffix
                else foreign_collection._convert_record(to_backend, value)
            )
        binary_mode = self._should_use_hex(field_name)

        return self._convert_value_helper(to_backend, field_name, binary_mode, value)

    def _convert_value_helper(self, to_backend: bool, path: str, use_hex: bool, value):
        if value and path in self._binary_fields:
            if isinstance(value, list):
                return [self._convert_value_helper(to_backend, path, use_hex, v) for v in value]

            return self._convert_scalar(to_backend, use_hex, value)
        return value

    def _convert_scalar(self, to_backend: bool, use_hex: bool, value):
        if to_backend:
            if isinstance(value, str):
                value = value.encode("ascii")
            value = hex2bytes(value) if use_hex else b64decode(value.split(b"base64,", 1)[1])

            return value

        if use_hex:
            return bytes2hex(value)

        if isinstance(value, str):
            value = value.encode("ascii")

        mime = filetype.guess(value)
        mime = mime.mime if mime is not None else "application/octet-stream"

        return f"data:{mime};base64," + b64encode(value).decode("ascii")

    def _replace_validation(self, field_name: str, field_schema: Column) -> List[Validation]:
        validations: List[Validation] = []

        if self._should_use_hex(field_name):
            validations.append({"operator": Operator.MATCH, "value": r"^[0-9a-f]+$"})

            min_length = [val for val in field_schema["validations"] if val["operator"] == Operator.LONGER_THAN]
            min_length = min_length[0]["value"] if len(min_length) > 0 else None
            if min_length:
                validations.append({"operator": Operator.LONGER_THAN, "value": min_length * 2 + 1})

            max_length = [val for val in field_schema["validations"] if val["operator"] == Operator.SHORTER_THAN]
            max_length = max_length[0]["value"] if len(max_length) > 0 else None
            if max_length:
                validations.append({"operator": Operator.SHORTER_THAN, "value": max_length * 2 - 1})
        else:
            validations.append({"operator": Operator.MATCH, "value": r"^data:.*;base64,.*"})

        present = [val for val in field_schema.get("validations", []) if val["operator"] == Operator.LONGER_THAN]
        if len(present) > 0:
            validations.append({"operator": Operator.PRESENT})

        return validations
