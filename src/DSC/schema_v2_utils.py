from typing import Dict, List, Literal

from forestadmin.agent_toolkit.utils.forest_schema.filterable import FrontendFilterableUtils
from forestadmin.agent_toolkit.utils.forest_schema.type import (
    ForestServerAction,
    ForestServerCollection,
    ForestServerField,
    ForestServerSegment,
    ServerValidationType,
)
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType
from typing_extensions import NotRequired, TypedDict


# TYPING
class SchemaV2Relation(TypedDict):
    name: str
    type: Literal["ManyToMany", "ManyToOne", "OneToOne", "OneToMany"]
    foreignCollection: str
    throughCollection: NotRequired[str]
    foreignKey: NotRequired[str]
    foreignKeyTarget: NotRequired[str]
    originKey: NotRequired[str]
    originKeyTarget: NotRequired[str]


class SchemaV2Field(TypedDict):
    name: str
    type: ColumnAlias
    filterOperators: List[str]
    # defaultValue: NotRequired[Any] # TODO
    # isRequired: NotRequired[Any] # TODO
    enumerations: NotRequired[List[str]]
    isPrimaryKey: NotRequired[bool]
    isWritable: NotRequired[bool]
    isSortable: NotRequired[bool]
    validations: NotRequired[List[ServerValidationType]]


class SchemaV2Collection(TypedDict):
    name: str
    fields: List[SchemaV2Field]  # to define
    relations: List  # to define
    segments: NotRequired[List[ForestServerSegment]]
    actions: NotRequired[List[ForestServerAction]]
    isSearchable: NotRequired[bool]
    canList: NotRequired[bool]
    canCreate: NotRequired[bool]
    canUpdate: NotRequired[bool]
    canDelete: NotRequired[bool]
    canCount: NotRequired[bool]
    canChart: NotRequired[bool]


# MASKS
SCHEMA_V2_FIELDS_MASK = {
    "enumerations": None,
    "isPrimaryKey": False,
    "isWritable": True,
    "isSortable": True,
    "validations": [],
}


SCHEMA_V2_COLLECTION_MASK = {
    "segments": [],
    "actions": [],
    "isSearchable": True,
    "canList": True,
    "canCreate": True,
    "canUpdate": True,
    "canDelete": True,
    "canCount": True,
    "canChart": True,
}


class SchemaV1toV2:
    def __init__(self, schema_collections: List[ForestServerCollection]) -> None:
        self.initial_schema: List[ForestServerCollection] = schema_collections

    def translate(self) -> List[SchemaV2Collection]:
        return self._convert_collection_schema_v1_to_v2(self.initial_schema)

    def _convert_collection_schema_v1_to_v2(
        self, schema_collections: List[ForestServerCollection]
    ) -> List[SchemaV2Collection]:
        schema_collections_v2: List[SchemaV2Collection] = []
        for collection_v1 in schema_collections:
            collection_v2: SchemaV2Collection = {
                "name": collection_v1["name"],
                "fields": self._convert_fields_v1_to_v2(collection_v1["fields"]),
                "relations": self._convert_fields_to_relation(collection_v1["fields"]),
                "actions": collection_v1["actions"],  # type:ignore
                "isSearchable": collection_v1["isSearchable"],
                "canList": True,
                "canCreate": not collection_v1["isReadOnly"],
                "canUpdate": not collection_v1["isReadOnly"],
                "canDelete": not collection_v1["isReadOnly"],
                "canCount": True,
                "canChart": True,
            }
            schema_collections_v2.append(self._template_reduce_collection(collection_v2))

        return schema_collections_v2

    def _convert_fields_v1_to_v2(self, fields: List[ForestServerField]) -> List[SchemaV2Field]:
        fields_v2: List[SchemaV2Field] = []
        for field_v1 in fields:
            if field_v1["relationship"] is not None:  # type:ignore
                continue

            fields_v2.append(
                self._template_reduce_field(
                    {
                        "name": field_v1["field"],  # type:ignore
                        "type": field_v1["type"],  # type:ignore
                        "filterOperators": [
                            op.value
                            for op in FrontendFilterableUtils.OPERATOR_BY_TYPES[
                                PrimitiveType(field_v1["field"])  # type:ignore
                            ]  # type:ignore
                        ],  # type:ignore
                        "enumerations": field_v1["enums"] if field_v1["type"] == "Enum" else None,  # type:ignore
                        "isPrimaryKey": field_v1["isPrimaryKey"],  # type:ignore
                        "isSortable": field_v1["isSortable"],  # type:ignore
                        "isWritable": not field_v1["isReadOnly"],  # type:ignore
                        "validations": field_v1["validations"],  # type:ignore
                    }
                )
            )

        return fields_v2

    def _convert_fields_to_relation(self, fields: List[ForestServerField]) -> List[SchemaV2Relation]:
        relation_v2: List[SchemaV2Relation] = []
        for field_v1 in fields:
            if field_v1["relationship"] is None:  # type:ignore
                continue

            relation: SchemaV2Relation = {
                "name": field_v1["field"],  # type:ignore
                "foreignCollection": field_v1["reference"].split(".")[0],  # type:ignore
            }  # type:ignore
            if field_v1["relationship"] == "BelongsTo":  # type:ignore
                relation = {
                    **relation,
                    "type": "ManyToOne",
                    "foreignKeyTarget": field_v1["reference"].split(".")[1],  # type:ignore
                    # TODO: may be impossible because v1 schema doesn't include foreign_keys
                    "foreignKey": "TODO: N/A",  # type:ignore
                    # doable in the case where it's the reverse of a 1to1
                }

            elif field_v1["relationship"] == "HasMany":  # type:ignore
                relation = {
                    **relation,
                    "type": "OneToMany",
                    "originKey": "",
                    # TODO: may be impossible because v1 schema doesn't include foreign_keys
                    "originKeyTarget": field_v1["reference"].split(".")[1],  # type:ignore # TODO: not sure about this
                }

            elif field_v1["relationship"] == "HasOne":  # type:ignore
                relation = {
                    **relation,
                    "type": "OneToOne",
                    "originKey": "",
                    "originKeyTarget": field_v1["reference"].split(".")[1],  # type:ignore
                }

            elif field_v1["relationship"] == "BelongsToMany":  # type:ignore
                reverse_relation = filter(  # type:ignore
                    lambda x: x["fields"] == field_v1["inverseOf"],  # type:ignore
                    self.initial_schema[relation["foreignCollection"]]["fields"],  # type:ignore
                )[0]

                relation = {
                    **relation,
                    "type": "ManyToMany",
                    "foreignKeyTarget": field_v1["reference"].split(".")[1],  # type:ignore
                    "originKeyTarget": reverse_relation["reference"].split(".")[1],
                    # TODO: may be impossible because v1 schema doesn't include foreign_keys
                    "originKey": "TODO: N/A",
                    "foreignKey": "TODO: N/A",
                    "throughCollection": "TODO: N/A",
                }
            relation_v2.append(relation)

        return relation_v2

    def _template_reduce_field(self, collection: SchemaV2Field) -> SchemaV2Field:
        return self._reduce_from_template(collection, SCHEMA_V2_FIELDS_MASK)  # type:ignore

    def _template_reduce_collection(self, collection: SchemaV2Collection) -> SchemaV2Collection:
        return self._reduce_from_template(collection, SCHEMA_V2_COLLECTION_MASK)  # type:ignore

    def _reduce_from_template(self, input, mask):
        reduced = {}
        for key, value in input:
            if key not in mask or input[key] != mask[key]:
                reduced[key] = value
        return reduced


class SchemaV2toV1:
    def __init__(self, schema_collections: List[SchemaV2Collection]) -> None:
        self.initial_schema = schema_collections

    def translate(self) -> List[ForestServerCollection]:
        return self._convert_collection_schema_v2_to_v1(self.initial_schema)

    def _get_value_or_default(self, instance, key, mask):
        return instance.get(key, mask[key])

    def collection_get_value_or_default(self, instance, key):
        return self._get_value_or_default(instance, key, SCHEMA_V2_COLLECTION_MASK)

    def field_get_value_or_default(self, instance, key):
        return self._get_value_or_default(instance, key, SCHEMA_V2_FIELDS_MASK)

    def _convert_collection_schema_v2_to_v1(
        self, collections_v2: List[SchemaV2Collection]
    ) -> List[ForestServerCollection]:
        schema_collections_v1: List[ForestServerCollection] = []
        for collection_v2 in collections_v2:
            schema_collections_v1.append(
                {
                    "name": collection_v2["name"],
                    "icon": None,
                    "integration": None,
                    "isVirtual": False,
                    "onlyForRelationships": False,
                    "paginationType": "page",
                    "fields": self.convert_fields_and_relation(collection_v2["fields"], collection_v2["relations"]),
                    "isReadOnly": not collection_v2.get("canCreate", SCHEMA_V2_COLLECTION_MASK["canCreate"]),
                    "isSearchable": collection_v2.get("isSearchable", SCHEMA_V2_COLLECTION_MASK["isSearchable"]),
                    "actions": collection_v2.get("actions", SCHEMA_V2_COLLECTION_MASK["actions"]),
                    "segments": collection_v2.get("segments", SCHEMA_V2_COLLECTION_MASK["segments"]),
                }
            )

        return schema_collections_v1

    def convert_fields_and_relation(
        self, fields: List[SchemaV2Field], relations: List[SchemaV2Relation]
    ) -> List[ForestServerField]:
        fields_v1: Dict[str, ForestServerField] = {}

        for field_v2 in fields:
            fields_v1[field_v2["name"]] = {
                "field": field_v2["name"],
                "type": field_v2["type"],
                "isPrimaryKey": field_v2.get("isPrimaryKey", SCHEMA_V2_FIELDS_MASK["isPrimaryKey"]),
                "isReadOnly": not field_v2.get("isWritable", SCHEMA_V2_FIELDS_MASK["isWritable"]),
                "isSortable": field_v2.get("isSortable", SCHEMA_V2_FIELDS_MASK["isSortable"]),
                # "defaultValue": None # TODO: need to handle this
                "isRequired": len(
                    [
                        *filter(
                            lambda x: x["type"] == "is present",
                            field_v2.get("validations", SCHEMA_V2_FIELDS_MASK["validations"]),
                        )
                    ]
                )
                > 0,  # type:ignore
                "enums": (
                    field_v2.get("enumerations", SCHEMA_V2_FIELDS_MASK["enumerations"])
                    if field_v2["type"] == "Enum"
                    else None
                ),
                "isFilterable": FrontendFilterableUtils.is_filterable(
                    field_v2["type"],
                    set([Operator(op) for op in field_v2["filterOperators"]]),
                ),
                "validations": field_v2.get("validations", SCHEMA_V2_FIELDS_MASK["validations"]),
                "integration": None,
                "isVirtual": False,
                "inverseOf": None,
                # "relationship": None, not set when it's a field
            }

        for rel_v2 in relations:
            name = rel_v2["name"]

            if rel_v2["type"] == "OneToMany":
                related_field_v2: SchemaV2Field = [
                    *filter(lambda x: x["name"] == rel_v2["originKey"], fields)  # type:ignore
                ][0]
                fields_v1[name] = {
                    **fields_v1[name],
                    "relationship": "HasMany",
                }

            elif rel_v2["type"] == "ManyToOne":
                foreign_collection_fields = [
                    *filter(lambda x: x["name"] == rel_v2["foreignCollection"], self.initial_schema)  # type:ignore
                ][0]["fields"]
                related_field_v2: SchemaV2Field = [
                    *filter(lambda x: x["name"] == rel_v2["foreignKey"], foreign_collection_fields)  # type:ignore
                ][0]

                fields_v1[name] = {
                    **fields_v1[name],
                    "relationship": "BelongsTo",
                }

            elif rel_v2["type"] == "OneToOne":
                related_field_v2: SchemaV2Field = [
                    *filter(lambda x: x["name"] == rel_v2["originKey"], fields)  # type:ignore
                ][0]
                fields_v1[name] = {
                    **fields_v1[name],
                    "relationship": "HasOne",
                }

            elif rel_v2["type"] == "ManyToMany":
                foreign_collection_fields = [
                    *filter(lambda x: x["name"] == rel_v2["foreignCollection"], self.initial_schema)  # type:ignore
                ][0]["fields"]
                related_field_v2: SchemaV2Field = [
                    *filter(lambda x: x["name"] == rel_v2["foreignKey"], foreign_collection_fields)  # type:ignore
                ][0]

                fields_v1[name] = {
                    **fields_v1[name],
                    "relationship": "BelongsToMany",
                }

            # fields_v1[rel_v2["name"]] = {
            #     "field": rel_v2["name"],
            #     "type": rel_v2["type"],
            #     "isPrimaryKey": rel_v2.get("isPrimaryKey", SCHEMA_V2_FIELDS_MASK["isPrimaryKey"]),
            #     "isReadOnly": not rel_v2.get("isWritable", SCHEMA_V2_FIELDS_MASK["isWritable"]),
            #     "isSortable": rel_v2.get("isSortable", SCHEMA_V2_FIELDS_MASK["isSortable"]),
            #     # "defaultValue": None # TODO: need to handle this
            #     "isRequired": len(
            #         [
            #             *filter(
            #                 lambda x: x["type"] == "is present",
            #                 rel_v2.get("validations", SCHEMA_V2_FIELDS_MASK["validations"]),
            #             )
            #         ]
            #     )
            #     > 0,  # type:ignore
            #     "enums": (
            #         rel_v2.get("enumerations", SCHEMA_V2_FIELDS_MASK["enumerations"])
            #         if rel_v2["type"] == "Enum"
            #         else None
            #     ),
            #     "isFilterable": FrontendFilterableUtils.is_filterable(
            #         rel_v2["type"],
            #         set([Operator(op) for op in rel_v2["filterOperators"]]),
            #     ),
            #     "validations": rel_v2.get("validations", SCHEMA_V2_FIELDS_MASK["validations"]),
            #     "integration": None,
            #     "isVirtual": False,
            #     "inverseOf": None,
            #     # "relationship": None, not set when it's a field
            # }

        return [*fields_v1.values()]
