import json
from typing import Any, Dict, List, Optional

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_sqlalchemy.utils.type_converter import Converter as TypeConverter
from forestadmin.datasource_sqlalchemy.utils.type_converter import FilterOperator
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    RelationAlias,
    Validation,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from sqlalchemy import ColumnDefault, Enum, Table
from sqlalchemy.orm import Mapper
from sqlalchemy.sql.schema import Column as SqlAlchemyColumn


class ColumnFactory:
    @staticmethod
    def _build_enum_values(column: SqlAlchemyColumn) -> Optional[List[str]]:
        if column.type.__class__ == Enum:  # type: ignore
            return column.type.enums  # type: ignore
        return None

    @staticmethod
    def _build_is_read_only(column: SqlAlchemyColumn) -> bool:
        return column.primary_key and column.autoincrement is not False  # type: ignore

    @classmethod
    def _build_validations(cls, column: SqlAlchemyColumn) -> List[Validation]:
        validations: List[Validation] = []
        if (
            not column.nullable
            and not cls._build_is_read_only(column)  # type: ignore
            and not column.default
            and not column.server_default  # type: ignore  # type: ignore
        ):
            validations.append(
                {
                    "operator": Operator.PRESENT,
                }
            )

        return validations

    @classmethod
    def build(cls, column: SqlAlchemyColumn) -> Column:
        column_type = TypeConverter.convert(column.type)  # type: ignore

        default_value = column.default.arg if isinstance(column.default, ColumnDefault) else column.default
        try:
            json.dumps(default_value)
        except TypeError:  # not JSON Serializable
            default_value = None

        return {
            "column_type": column_type,
            "is_primary_key": column.primary_key,  # type: ignore
            "is_read_only": cls._build_is_read_only(column),
            "default_value": default_value,
            "is_sortable": True,
            "validations": cls._build_validations(column),
            "filter_operators": FilterOperator.get_for_type(column_type),
            "enum_values": cls._build_enum_values(column),
            "type": FieldType.COLUMN,
        }


def is_composite_fk(relation: Any):
    return len(relation.remote_side) > 1 or len(relation.local_columns) > 1


class CollectionFactory:
    @staticmethod
    def _build_one_to_many(relation: Any) -> Optional[OneToMany]:
        if is_composite_fk(relation):
            return None
        return {
            "foreign_collection": relation.target.name,
            "origin_key": list(relation.remote_side)[0].name,
            "origin_key_target": list(relation.local_columns)[0].name,
            "type": FieldType.ONE_TO_MANY,
        }

    @staticmethod
    def _build_many_to_one(relation: Any) -> Optional[ManyToOne]:
        if is_composite_fk(relation):
            return None
        return {
            "foreign_collection": relation.target.name,
            "foreign_key": list(relation.local_columns)[0].name,
            "foreign_key_target": relation.target.primary_key.columns[0].name,
            "type": FieldType.MANY_TO_ONE,
        }

    @staticmethod
    def _build_one_to_one(relation: Any) -> Optional[OneToOne]:
        if is_composite_fk(relation):
            return None
        return {
            "foreign_collection": relation.target.name,
            "origin_key": list(relation.remote_side)[0].name,
            "origin_key_target": list(relation.local_columns)[0].name,
            "type": FieldType.ONE_TO_ONE,
        }

    @staticmethod
    def _build_many_to_many(model: Table, relation: Any) -> Optional[ManyToMany]:
        kwargs: Dict[str, str] = {}
        for column in relation.remote_side:
            if len(column.foreign_keys) > 1:  # composite fk
                return None
            fk = list(column.foreign_keys)[0]
            if fk.column.table.name == model.name:
                kwargs["origin_key_target"] = fk.column.name
                kwargs["origin_key"] = column.name
            else:
                kwargs["foreign_key_target"] = fk.column.name
                kwargs["foreign_key"] = column.name
                kwargs["foreign_collection"] = fk.column.table.name
        return ManyToMany(
            **{
                "through_collection": relation.secondary.name,  # type: ignore
                "type": FieldType.MANY_TO_MANY,  # type: ignore
                "foreign_relation": None,  # type: ignore
                **kwargs,
            }
        )

    @classmethod
    def build(cls, model: Table, mapper: Optional[Mapper] = None) -> CollectionSchema:
        fields = {}
        for column in model.columns:  # type: ignore
            fields[column.name] = ColumnFactory.build(column)  # type: ignore

        if mapper:
            for name, relationship in mapper.relationships.items():  # type: ignore
                relation: Optional[RelationAlias] = None
                if relationship.direction.name == "MANYTOMANY":
                    relation = cls._build_many_to_many(model, relationship)

                elif relationship.direction.name == "ONETOMANY":
                    if relationship.uselist:
                        relation = cls._build_one_to_many(relationship)
                    else:
                        relation = cls._build_one_to_one(relationship)

                elif relationship.direction.name == "MANYTOONE":
                    relation = cls._build_many_to_one(relationship)

                # if not relationship.back_populates:  # type: ignore
                #     # one to many
                #     relation = cls._build_one_to_many(relationship)
                # else:
                #     if relationship.uselist is False:  # type: ignore
                #         if list(relationship.local_columns)[0].foreign_keys:  # type: ignore
                #             relation = cls._build_many_to_one(relationship)
                #         else:
                #             relation = cls._build_one_to_one(relationship)
                #     elif relationship.secondary is not None:  # type: ignore
                #         relation = cls._build_many_to_many(model, relationship)
                #     else:
                #         relation = cls._build_one_to_many(relationship)

                if relation is not None:
                    fields[relationship.key] = relation  # type: ignore
                else:
                    ForestLogger.log("error", f"A relation is not handled during introspection: {model.name}.{name} ")

        return {"actions": {}, "fields": fields, "searchable": False, "segments": []}
