from datetime import date, datetime, time, timezone
from unittest import TestCase, skip
from uuid import UUID

from forestadmin.agent_toolkit.services.serializers.exceptions import JsonApiDeserializerException
from forestadmin.agent_toolkit.services.serializers.json_api_deserializer import JsonApiDeserializer
from forestadmin.agent_toolkit.services.serializers.json_api_serializer import JsonApiSerializer
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    PolymorphicManyToOne,
    PolymorphicOneToMany,
    PolymorphicOneToOne,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory


class TestJsonApi(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class # type:ignore

        cls.collection_person = Collection("Person", cls.datasource)  # type:ignore
        cls.collection_person.add_fields(
            {
                "person_pk": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "first_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    is_sortable=True,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    is_primary_key=False,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "last_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    is_sortable=True,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    is_primary_key=False,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "birthday": Column(
                    column_type=PrimitiveType.DATE_ONLY,
                    type=FieldType.COLUMN,
                    is_sortable=True,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    is_primary_key=False,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "orders": OneToMany(
                    foreign_collection="Order",
                    origin_key="person_id",
                    origin_key_target="person_pk",
                    type=FieldType.ONE_TO_MANY,
                ),
                "profile": OneToOne(
                    foreign_collection="Profile",
                    origin_key="person_id",
                    origin_key_target="person_pk",
                    type=FieldType.ONE_TO_ONE,
                ),
            }
        )

        cls.collection_profile = Collection("Profile", cls.datasource)  # type:ignore
        cls.collection_profile.add_fields(
            {
                "profile_pk": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "person_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "data": Column(
                    column_type=PrimitiveType.JSON,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "person": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="person_id",
                    foreign_key_target="person_pk",
                    type=FieldType.MANY_TO_ONE,
                ),
                "picture": PolymorphicOneToOne(
                    foreign_collection="Picture",
                    origin_key="target_id",
                    origin_key_target="profile_pk",
                    origin_type_field="target_type",
                    origin_type_value="Product",
                    type=FieldType.POLYMORPHIC_ONE_TO_ONE,
                ),
                "comments": PolymorphicOneToMany(
                    foreign_collection="Comment",
                    origin_key="target_id",
                    origin_key_target="profile_pk",
                    origin_type_field="target_type",
                    origin_type_value="Product",
                    type=FieldType.POLYMORPHIC_ONE_TO_MANY,
                ),
            }
        )

        cls.collection_order = Collection("Order", cls.datasource)  # type:ignore
        cls.collection_order.add_fields(
            {
                "order_pk": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "customer_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "customer": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="customer_id",
                    foreign_key_target="person_pk",
                    type=FieldType.MANY_TO_ONE,
                ),
                "products": ManyToMany(
                    foreign_collection="Product",
                    foreign_key="product_id",
                    foreign_key_target="product_pk",
                    origin_key="order_id",
                    origin_key_target="order_pk",
                    through_collection="OrderProducts",
                    foreign_relation="orders",
                    type=FieldType.MANY_TO_MANY,
                ),
                "order_products": OneToMany(
                    foreign_collection="OrderProducts",
                    origin_key="order_id",
                    origin_key_target="order_pk",
                    type=FieldType.ONE_TO_MANY,
                ),
            }
        )

        cls.collection_order_products = Collection("OrderProducts", cls.datasource)  # type:ignore
        cls.collection_order_products.add_fields(
            {
                "order_id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "product_id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "orders": ManyToOne(
                    foreign_collection="Order",
                    foreign_key="order_id",
                    foreign_key_target="order_pk",
                    type=FieldType.MANY_TO_ONE,
                ),
            }
        )

        cls.collection_product = Collection("Product", cls.datasource)  # type:ignore
        cls.collection_product.add_fields(
            {
                "product_pk": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "price": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                    is_sortable=True,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    is_primary_key=False,
                    filter_operators=set([Operator.EQUAL, Operator.IN, Operator.GREATER_THAN]),
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "label": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    is_sortable=True,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    is_primary_key=False,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "date_online": Column(
                    column_type=PrimitiveType.DATE,
                    type=FieldType.COLUMN,
                    is_sortable=True,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    is_primary_key=False,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    validations=[{"operator": Operator.PRESENT}],
                ),
                "orders": ManyToMany(
                    foreign_collection="Product",
                    origin_key="product_id",
                    origin_key_target="product_pk",
                    foreign_key="order_id",
                    foreign_key_target="order_pk",
                    through_collection="OrderProducts",
                    foreign_relation="products",
                    type=FieldType.MANY_TO_MANY,
                ),
                "picture": PolymorphicOneToOne(
                    foreign_collection="Picture",
                    origin_key="target_id",
                    origin_key_target="product_pk",
                    origin_type_field="target_type",
                    origin_type_value="Product",
                    type=FieldType.POLYMORPHIC_ONE_TO_ONE,
                ),
                "comments": PolymorphicOneToMany(
                    foreign_collection="Comment",
                    origin_key="target_id",
                    origin_key_target="product_pk",
                    origin_type_field="target_type",
                    origin_type_value="Product",
                    type=FieldType.POLYMORPHIC_ONE_TO_MANY,
                ),
            }
        )

        cls.collection_picture = Collection("Picture", cls.datasource)  # type:ignore
        cls.collection_picture.add_fields(
            {
                "picture_pk": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "image": Column(
                    column_type=PrimitiveType.BINARY,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=False,
                    validations=[],
                ),
                "target_id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "target_type": Column(
                    column_type=PrimitiveType.ENUM,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=["Product", "Profile"],
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "target_object": PolymorphicManyToOne(
                    foreign_collections=["Product", "Profile"],
                    foreign_key="target_id",
                    foreign_key_type_field="target_type",
                    foreign_key_targets={"Product": "product_pk", "Profile": "profile_pk"},
                    type=FieldType.POLYMORPHIC_MANY_TO_ONE,
                ),
            }
        )

        cls.collection_comment = Collection("Comment", cls.datasource)  # type:ignore
        cls.collection_comment.add_fields(
            {
                "comment_pk": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "comment": Column(
                    column_type=PrimitiveType.STRING,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=False,
                    validations=[],
                ),
                "target_id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "target_type": Column(
                    column_type=PrimitiveType.ENUM,
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=["Product", "Profile"],
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "target_object": PolymorphicManyToOne(
                    foreign_collections=["Product", "Profile"],
                    foreign_key="target_id",
                    foreign_key_type_field="target_type",
                    foreign_key_targets={"Product": "product_pk", "Profile": "profile_pk"},
                    type=FieldType.POLYMORPHIC_MANY_TO_ONE,
                ),
            }
        )

        cls.collection_all_types = Collection("AllTypes", cls.datasource)  # type:ignore
        cls.collection_all_types.add_fields(
            {
                "all_types_pk": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "comment": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "enum": Column(column_type="Enum", type="Column", enum_values=["a", "b", "c"]),
                "bool": Column(column_type="Boolean", type="Column"),
                "int": Column(column_type="Number", type="Column"),
                "float": Column(column_type="Number", type="Column"),
                "datetime": Column(column_type="Date", type="Column"),
                "dateonly": Column(column_type="Dateonly", type="Column"),
                "time_only": Column(column_type="Timeonly", type="Column"),
                "point": Column(column_type="Point", type="Column"),
                "binary": Column(column_type="String", type="Column"),
                "json": Column(column_type="Json", type="Column"),
                "custom": Column(column_type=[{"id": "Number"}], type="Column"),
            }
        )

        cls.collection_str_pk = Collection("StrPK", cls.datasource)  # type:ignore
        cls.collection_str_pk.add_fields(
            {
                "pk": Column(
                    column_type=PrimitiveType.STRING,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "name": Column(column_type="String", type="Column"),
                "relation_pk": Column(column_type="String", type="Column"),
                "relation": ManyToOne(
                    foreign_collection="StrPKRelation",
                    foreign_key="relation_pk",
                    foreign_key_target="pk",
                    type=FieldType.MANY_TO_ONE,
                ),
            }
        )

        cls.collection_str_pk_relation = Collection("StrPKRelation", cls.datasource)  # type:ignore
        cls.collection_str_pk_relation.add_fields(
            {
                "pk": Column(
                    column_type=PrimitiveType.STRING,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=False,
                    default_value=None,
                    enum_values=None,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=True,
                    validations=[],
                ),
                "name": Column(column_type="String", type="Column"),
            }
        )

        cls.datasource.add_collection(cls.collection_order)
        cls.datasource.add_collection(cls.collection_order_products)
        cls.datasource.add_collection(cls.collection_product)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_profile)
        cls.datasource.add_collection(cls.collection_picture)
        cls.datasource.add_collection(cls.collection_comment)
        cls.datasource.add_collection(cls.collection_all_types)
        cls.datasource.add_collection(cls.collection_str_pk)
        cls.datasource.add_collection(cls.collection_str_pk_relation)


class TestJsonApiDeserializer(TestJsonApi):
    def test_should_correctly_load_attributes(self):
        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {
                    "price": 2.23,
                    "label": "strawberries",
                    "date_online": "2023-10-10T10:10:10+00:00",
                },
                "type": "Product",
            }
        }

        data = JsonApiDeserializer(self.datasource).deserialize(request_body, self.collection_product)
        self.assertEqual(
            data,
            {
                "price": 2.23,
                "label": "strawberries",
                "date_online": datetime(2023, 10, 10, 10, 10, 10, tzinfo=timezone.utc),
            },
        )

    def test_should_correctly_load_all_types_of_data(self):
        deserializer = JsonApiDeserializer(self.datasource)

        request_body = {
            "data": {
                "id": "b2f47557-8518-4e55-a02b-ed92d113d42d",
                "attributes": {
                    "all_types_pk": "b2f47557-8518-4e55-a02b-ed92d113d42f",
                    "comment": "record 1",
                    "enum": "a",
                    "bool": True,
                    "int": 10,
                    "float": 22,
                    "datetime": "2025-02-03T14:54:56.000255+00:00",
                    "dateonly": "2025-02-01",
                    "time_only": "15:35:25",
                    "point": "12,14",
                    "binary": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElE"
                    "QVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==",
                    "custom": [{"id": 1}],
                    "json": {"a": "a", "b": 2, "c": []},
                },
                "type": "AllTypes",
            }
        }
        data = deserializer.deserialize(request_body, self.collection_all_types)
        self.assertEqual(
            data,
            {
                "all_types_pk": UUID("b2f47557-8518-4e55-a02b-ed92d113d42f"),
                "comment": "record 1",
                "enum": "a",
                "bool": True,
                "int": 10,
                "float": 22,
                "datetime": datetime(2025, 2, 3, 14, 54, 56, 255, timezone.utc),
                "dateonly": date(2025, 2, 1),
                "time_only": time(15, 35, 25),
                "point": [12, 14],
                "binary": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElE"
                "QVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==",
                "custom": [{"id": 1}],
                "json": {"a": "a", "b": 2, "c": []},
            },
        )

    def test_should_correctly_load_int_or_float_from_string_value(self):
        deserializer = JsonApiDeserializer(self.datasource)
        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {
                    "price": "2.23",
                },
                "type": "Product",
            }
        }
        data = deserializer.deserialize(request_body, self.collection_product)
        self.assertEqual(
            data,
            {
                "price": 2.23,
            },
        )

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {
                    "price": "10",
                    "label": None,
                },
                "type": "Product",
            }
        }

        data = deserializer.deserialize(request_body, self.collection_product)
        self.assertEqual(
            data,
            {
                "price": 10,
                "label": None,
            },
        )

    def test_should_correctly_load_many_to_one_relationship(self):
        deserializer = JsonApiDeserializer(self.datasource)

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Orders",
                "relationships": {"customer": {"data": {"id": "12", "type": "Persons"}}},
            }
        }
        data = deserializer.deserialize(request_body, self.collection_order)
        self.assertEqual(
            data,
            {
                "customer": 12,
            },
        )

    @skip("Front end never send toMany relationships")
    def test_should_correctly_load_to_many_relations(self):
        deserializer = JsonApiDeserializer(self.datasource)

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Orders",
                "relationships": {
                    "products": {
                        "data": [
                            {"type": "Products", "id": "0086ebe0-3452-4779-91de-26d14850998c"},
                            {"type": "Products", "id": "68dcab0f-2dec-468f-8ebd-ff2752d24b81"},
                        ]
                    },
                    "order_products": {
                        "data": [
                            {
                                "type": "OrderProducts",
                                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7|833a6308-da81-4363-9448-d101eb593d94",
                            },
                            {
                                "type": "OrderProducts",
                                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7|9f9348fe-3d2d-43be-b0be-ff58313b137e",
                            },
                        ]
                    },
                },
            }
        }
        data = deserializer.deserialize(request_body, self.collection_order)
        self.assertEqual(
            data,
            {
                "products": ["0086ebe0-3452-4779-91de-26d14850998c", "68dcab0f-2dec-468f-8ebd-ff2752d24b81"],
                "order_products": ["833a6308-da81-4363-9448-d101eb593d94", "9f9348fe-3d2d-43be-b0be-ff58313b137e"],
                "order_pk": UUID("43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7"),
                # "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
            },
        )

    def test_should_not_deserialize_toMany_relations(self):
        deserializer = JsonApiDeserializer(self.datasource)

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Orders",
                "relationships": {
                    "products": {
                        "data": [
                            {"type": "Products", "id": "0086ebe0-3452-4779-91de-26d14850998c"},
                        ]
                    }
                },
            }
        }
        self.assertRaisesRegex(
            JsonApiDeserializerException,
            "We shouldn't deserialize toMany relations",
            deserializer.deserialize,
            request_body,
            self.collection_order,
        )

    def test_should_correctly_load_polymorphic_many_to_one_relation(self):
        deserializer = JsonApiDeserializer(self.datasource)
        request_body = {
            "data": {
                "type": "Comments",
                "attributes": {
                    "comment": "I like it a lot.",
                },
                "relationships": {
                    "target_object": {
                        "data": {
                            "type": "Product",
                            "id": "1806bdb7-5db4-46a1-acca-9a00f8a670dd",
                        },
                    }
                },
            }
        }

        data = deserializer.deserialize(request_body, self.collection_comment)
        self.assertEqual(
            data,
            {
                "target_id": UUID("1806bdb7-5db4-46a1-acca-9a00f8a670dd"),
                "target_type": "Product",
                "comment": "I like it a lot.",
            },
        )

    def test_should_ignore_null_many_to_one_relations(self):
        deserializer = JsonApiDeserializer(self.datasource)
        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Orders",
                "relationships": {"customer": {"data": None}},
            }
        }
        data = deserializer.deserialize(request_body, self.collection_order)
        self.assertEqual(data, {"customer": None})

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Orders",
                "relationships": {"customer": {"data": {}}},
            }
        }
        data = deserializer.deserialize(request_body, self.collection_order)
        self.assertEqual(data, {"customer": None})

    def test_should_correctly_load_polymorphic_one_to_one_relation(self):
        deserializer = JsonApiDeserializer(self.datasource)

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Profile",
                "relationships": {
                    "picture": {"data": {"id": "34d0adfe-823d-4fb4-9c3e-ac241887aa1c", "type": "Picture"}}
                },
            }
        }
        data = deserializer.deserialize(request_body, self.collection_profile)
        self.assertEqual(
            data,
            {
                "picture": UUID("34d0adfe-823d-4fb4-9c3e-ac241887aa1c"),
            },
        )

    def test_should_correctly_load_one_to_one_relation(self):
        deserializer = JsonApiDeserializer(self.datasource)

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "person",
                "relationships": {"profile": {"data": {"id": "12", "type": "Profile"}}},
            }
        }
        data = deserializer.deserialize(request_body, self.collection_person)
        self.assertEqual(
            data,
            {
                "profile": 12,
            },
        )


class TestJsonApiSerializer(TestJsonApi):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.person_records = [
            {
                "person_pk": 12,
                "first_name": "henry",
                "last_name": "calvill",
                "birthday": date(1974, 10, 1),
                "orders": [],
                "profile": None,
            }
        ]
        cls.order_records = [
            {
                "order_pk": "825dfdf9-1339-4373-af7b-261d99b09622",
                "customer_id": None,
                "customer": None,
                "products": [],
            }
        ]
        cls.product_records = [
            {
                "product_pk": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                "price": 2.23,
                "label": "strawberries",
                "date_online": datetime(2023, 10, 10, 10, 10, 10, 0, tzinfo=timezone.utc),
                "orders": [],
                "comments": [],
                "picture": None,
            },
            {
                "product_pk": "d1b8d706-46fa-4ae6-8015-8240b0603dfe",
                "price": 9.99,
                "label": "stick",
                "date_online": datetime(2023, 10, 10, 8, 8, 10, 0, tzinfo=timezone.utc),
                "orders": [],
                "comments": [],
                "picture": None,
            },
        ]
        cls.comments_records = [
            {
                "comment_pk": "0b622590-c823-4d2f-84e6-bbbdd31c8af8",
                "comment": "very good",
                "target_id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                "target_type": "Product",
                "target_object": {**cls.product_records[0]},
            },
            {
                "comment_pk": "60908a3e-97d7-4518-a724-17359e05c9e2",
                "comment": "very bad",
                "target_id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                "target_type": "Profile",
                "target_object": {
                    "profile_pk": "913b45d2-712e-4f93-a1e8-79519ef756bf",
                    "data": {"my_custom_data": "value"},
                    "person_id": 12,
                },
            },
        ]
        cls.all_types_records = [
            {
                "all_types_pk": UUID("b2f47557-8518-4e55-a02b-ed92d113d42f"),
                "comment": "record 1",
                "enum": "a",
                "bool": True,
                "int": 10,
                "float": 22.3,
                "datetime": datetime(2025, 2, 3, 14, 54, 56, 255, timezone.utc),
                "dateonly": date(2025, 2, 1),
                "time_only": time(15, 35, 25),
                "point": [12, 14],
                "json": [{"a": "a", "b": 2, "c": []}],
                "binary": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/"
                "w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==",
                "custom": [{"id": 1}],
            },
            {
                "all_types_pk": "c578ccd6-3dd0-4315-87f3-e200d80dd6f9",
                "comment": "record 1",
                "enum": "b",
                "bool": False,
                "int": None,
                "float": None,
                "datetime": datetime(2025, 2, 3, 14, 54, 56, 255, timezone.utc).isoformat(),
                "dateonly": date(2025, 2, 1).isoformat(),
                "time_only": time(15, 35, 25).isoformat(),
                "point": (12, 14),
                "json": {"a": "a", "b": 2, "c": []},
                "binary": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/"
                "w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==",
                "custom": [{"id": 2}],
            },
        ]

    def test_should_correctly_dump_attributes_according_to_projection(self):
        projection = ProjectionFactory.all(self.collection_product, allow_nested=False)
        dumped = JsonApiSerializer(self.datasource, projection).serialize(self.product_records, self.collection_product)

        self.assertEqual(
            dumped,
            {
                "data": [
                    {
                        "type": "Product",
                        "id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                        "attributes": {
                            "product_pk": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                            "price": 2.23,
                            "label": "strawberries",
                            "date_online": "2023-10-10T10:10:10+00:00",
                        },
                        "links": {"self": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af"},
                    },
                    {
                        "type": "Product",
                        "id": "d1b8d706-46fa-4ae6-8015-8240b0603dfe",
                        "attributes": {
                            "product_pk": "d1b8d706-46fa-4ae6-8015-8240b0603dfe",
                            "price": 9.99,
                            "label": "stick",
                            "date_online": "2023-10-10T08:08:10+00:00",
                        },
                        "links": {"self": "/forest/Product/d1b8d706-46fa-4ae6-8015-8240b0603dfe"},
                    },
                ]
            },
        )

    def test_should_correctly_dump_all_data_types(self):
        projection = ProjectionFactory.all(self.collection_all_types, allow_nested=False)
        serializer = JsonApiSerializer(self.datasource, projection)
        dumped = serializer.serialize(self.all_types_records, self.collection_all_types)
        self.assertEqual(
            dumped,
            {
                "data": [
                    {
                        "type": "AllTypes",
                        "id": "b2f47557-8518-4e55-a02b-ed92d113d42f",
                        "attributes": {
                            "all_types_pk": "b2f47557-8518-4e55-a02b-ed92d113d42f",
                            "comment": "record 1",
                            "enum": "a",
                            "bool": True,
                            "int": 10,
                            "float": 22.3,
                            "datetime": "2025-02-03T14:54:56.000255+00:00",
                            "time_only": "15:35:25",
                            "dateonly": "2025-02-01",
                            "point": [12, 14],
                            "binary": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElE"
                            "QVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==",
                            "json": [{"a": "a", "b": 2, "c": []}],
                            "custom": [{"id": 1}],
                        },
                        "links": {"self": "/forest/AllTypes/b2f47557-8518-4e55-a02b-ed92d113d42f"},
                    },
                    {
                        "type": "AllTypes",
                        "id": "c578ccd6-3dd0-4315-87f3-e200d80dd6f9",
                        "attributes": {
                            "all_types_pk": "c578ccd6-3dd0-4315-87f3-e200d80dd6f9",
                            "comment": "record 1",
                            "enum": "b",
                            "bool": False,
                            "int": None,
                            "float": None,
                            "datetime": "2025-02-03T14:54:56.000255+00:00",
                            "time_only": "15:35:25",
                            "dateonly": "2025-02-01",
                            "point": (12, 14),
                            "binary": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHE"
                            "lEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg==",
                            "json": {"a": "a", "b": 2, "c": []},
                            "custom": [{"id": 2}],
                        },
                        "links": {"self": "/forest/AllTypes/c578ccd6-3dd0-4315-87f3-e200d80dd6f9"},
                    },
                ]
            },
        )

    def test_should_correctly_dump_int_or_float_from_string_value(self):
        projection = ProjectionFactory.all(self.collection_product, allow_nested=False)
        serializer = JsonApiSerializer(self.datasource, projection)

        records = [
            {**self.product_records[0]},
            {**self.product_records[1]},
        ]
        records[0]["price"] = "2.23"
        records[1]["price"] = "10"

        dumped = serializer.serialize(records, self.collection_product)
        self.assertEqual(
            dumped,
            {
                "data": [
                    {
                        "type": "Product",
                        "id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                        "attributes": {
                            "product_pk": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                            "price": 2.23,
                            "label": "strawberries",
                            "date_online": "2023-10-10T10:10:10+00:00",
                        },
                        "links": {"self": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af"},
                    },
                    {
                        "type": "Product",
                        "id": "d1b8d706-46fa-4ae6-8015-8240b0603dfe",
                        "attributes": {
                            "product_pk": "d1b8d706-46fa-4ae6-8015-8240b0603dfe",
                            "price": 10,
                            "label": "stick",
                            "date_online": "2023-10-10T08:08:10+00:00",
                        },
                        "links": {"self": "/forest/Product/d1b8d706-46fa-4ae6-8015-8240b0603dfe"},
                    },
                ]
            },
        )

    def test_should_correctly_dump_many_to_one_according_to_projection(self):
        record = {**self.order_records[0]}
        record["customer"] = {**self.person_records[0]}
        record["customer_id"] = record["customer"]["person_pk"]
        dumped = JsonApiSerializer(
            self.datasource, Projection("order_pk", "customer_id", "customer:person_pk", "customer:first_name")
        ).serialize(record, self.collection_order)

        self.assertEqual(
            dumped,
            {
                "data": {
                    "type": "Order",
                    "id": "825dfdf9-1339-4373-af7b-261d99b09622",
                    "attributes": {
                        "order_pk": "825dfdf9-1339-4373-af7b-261d99b09622",
                        "customer_id": 12,
                    },
                    "relationships": {
                        "customer": {
                            "links": {
                                "related": {
                                    "href": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622/relationships/customer"
                                }
                            },
                            "data": {"type": "Person", "id": "12"},
                        }
                    },
                    "links": {"self": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622"},
                },
                "links": {"self": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622"},
                "included": [
                    {
                        "type": "Person",
                        "attributes": {"person_pk": 12, "first_name": "henry"},
                        "id": 12,
                        "links": {"self": "/forest/Person/12"},
                    }
                ],
            },
        )

    def test_should_correctly_dump_to_many_according_to_projection(self):
        """
        toMany relations should not be serialize (and it's not by the datasource)
        the only think to do is to fill [data/relationships/$relation/links/related/href]
        """

        record = {**self.order_records[0]}
        record["customer_id"] = self.person_records[0]["person_pk"]
        record["products"] = None
        record["order_products"] = None

        dumped = JsonApiSerializer(
            self.datasource,
            Projection(
                "order_pk",
                "customer_id",
                "products:label",
                "products:price",
                "products:product_pk",
                "order_products:product_id",
            ),
        ).serialize(record, self.collection_order)

        self.assertEqual(
            dumped,
            {
                "data": {
                    "type": "Order",
                    "id": "825dfdf9-1339-4373-af7b-261d99b09622",
                    "attributes": {
                        "order_pk": "825dfdf9-1339-4373-af7b-261d99b09622",
                        "customer_id": 12,
                    },
                    "relationships": {
                        "products": {
                            "links": {
                                "related": {
                                    "href": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622/relationships/products"
                                }
                            },
                            "data": [],
                        },
                        "order_products": {
                            "links": {
                                "related": {
                                    "href": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622/"
                                    "relationships/order_products"
                                }
                            },
                            "data": [],
                        },
                    },
                    "links": {"self": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622"},
                },
                "links": {"self": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622"},
            },
        )

    def test_should_correctly_dump_polymorphic_many_to_one(self):
        dumped = JsonApiSerializer(
            self.datasource, Projection("comment_pk", "comment", "target_id", "target_type", "target_object:*")
        ).serialize(self.comments_records, self.collection_comment)

        self.assertEqual(
            dumped,
            {
                "data": [
                    {
                        "type": "Comment",
                        "id": "0b622590-c823-4d2f-84e6-bbbdd31c8af8",
                        "attributes": {
                            "comment_pk": "0b622590-c823-4d2f-84e6-bbbdd31c8af8",
                            "target_type": "Product",
                            "target_id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                            "comment": "very good",
                        },
                        "relationships": {
                            "target_object": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Comment/0b622590-c823-4d2f-84e6-bbbdd31c8af8/"
                                        "relationships/target_object"
                                    }
                                },
                                "data": {
                                    "type": "Product",
                                    "id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                                },
                            }
                        },
                        "links": {"self": "/forest/Comment/0b622590-c823-4d2f-84e6-bbbdd31c8af8"},
                    },
                    {
                        "type": "Comment",
                        "id": "60908a3e-97d7-4518-a724-17359e05c9e2",
                        "attributes": {
                            "comment_pk": "60908a3e-97d7-4518-a724-17359e05c9e2",
                            "target_id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                            "target_type": "Profile",
                            "comment": "very bad",
                        },
                        "relationships": {
                            "target_object": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Comment/60908a3e-97d7-4518-a724-17359e05c9e2/"
                                        "relationships/target_object"
                                    }
                                },
                                "data": {"type": "Profile", "id": "913b45d2-712e-4f93-a1e8-79519ef756bf"},
                            }
                        },
                        "links": {"self": "/forest/Comment/60908a3e-97d7-4518-a724-17359e05c9e2"},
                    },
                ],
                "included": [
                    {
                        "type": "Product",
                        "attributes": {
                            "product_pk": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                            "price": 2.23,
                            "label": "strawberries",
                            "date_online": "2023-10-10T10:10:10+00:00",
                        },
                        "relationships": {
                            "orders": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af/"
                                        "relationships/orders"
                                    }
                                }
                            },
                            "picture": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af/"
                                        "relationships/picture"
                                    }
                                }
                            },
                            "comments": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af/"
                                        "relationships/comments"
                                    }
                                }
                            },
                        },
                        "id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                        "links": {"self": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af"},
                    },
                    {
                        "type": "Profile",
                        "id": "913b45d2-712e-4f93-a1e8-79519ef756bf",
                        "attributes": {
                            "profile_pk": "913b45d2-712e-4f93-a1e8-79519ef756bf",
                            "person_id": 12,
                            "data": {"my_custom_data": "value"},
                        },
                        "relationships": {
                            "person": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf/"
                                        "relationships/person"
                                    }
                                }
                            },
                            "picture": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf/"
                                        "relationships/picture"
                                    }
                                }
                            },
                            "comments": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf/"
                                        "relationships/comments"
                                    }
                                }
                            },
                        },
                        "links": {"self": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf"},
                    },
                ],
            },
        )

    def test_should_ignore_polymorphic_many_to_one_if_type_is_unknown(self):
        records = [{**self.comments_records[0], "target_type": "Unknown"}]
        dumped = JsonApiSerializer(
            self.datasource, Projection("comment_pk", "comment", "target_id", "target_type", "target_object:*")
        ).serialize(records, self.collection_comment)

        self.assertEqual(
            dumped,
            {
                "data": [
                    {
                        "type": "Comment",
                        "id": "0b622590-c823-4d2f-84e6-bbbdd31c8af8",
                        "attributes": {
                            "comment_pk": "0b622590-c823-4d2f-84e6-bbbdd31c8af8",
                            "target_type": "Unknown",
                            "target_id": "8f6834d7-845f-421c-ac8a-76fd9b5895af",
                            "comment": "very good",
                        },
                        "relationships": {
                            "target_object": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Comment/0b622590-c823-4d2f-84e6-bbbdd31c8af8/"
                                        "relationships/target_object"
                                    }
                                },
                                "data": None,
                            }
                        },
                        "links": {"self": "/forest/Comment/0b622590-c823-4d2f-84e6-bbbdd31c8af8"},
                    },
                ],
            },
        )

    def test_string_primary_keys_should_be_url_encoded(self):
        serializer = JsonApiSerializer(self.datasource, Projection("pk", "name"))
        record = {"pk": "hello/world", "name": "hello world"}
        dumped = serializer.serialize(record, self.collection_str_pk)
        self.assertEqual(
            dumped,
            {
                "data": {
                    "type": "StrPK",
                    "id": "hello%2Fworld",
                    "attributes": {"pk": "hello/world", "name": "hello world"},
                    "links": {"self": "/forest/StrPK/hello%2Fworld"},
                },
                "links": {"self": "/forest/StrPK/hello%2Fworld"},
            },
        )

    def test_string_foreign_keys_should_be_url_encoded_so_foreign_pk(self):
        serializer = JsonApiSerializer(
            self.datasource, Projection("pk", "name", "relation_pk", "relation:pk", "relation:name")
        )
        record = {
            "pk": "hello/world",
            "name": "hello world",
            "relation_pk": "hello/other/people",
            "relation": {"pk": "hello/other/people", "name": "hello other people"},
        }
        dumped = serializer.serialize(record, self.collection_str_pk)
        self.assertEqual(
            dumped,
            {
                "data": {
                    "type": "StrPK",
                    "id": "hello%2Fworld",
                    "attributes": {"pk": "hello/world", "name": "hello world", "relation_pk": "hello/other/people"},
                    "links": {"self": "/forest/StrPK/hello%2Fworld"},
                    "relationships": {
                        "relation": {
                            "data": {"id": "hello%2Fother%2Fpeople", "type": "StrPKRelation"},
                            "links": {"related": {"href": "/forest/StrPK/hello%2Fworld/relationships/relation"}},
                        }
                    },
                },
                "links": {"self": "/forest/StrPK/hello%2Fworld"},
                "included": [
                    {
                        "id": "hello%2Fother%2Fpeople",
                        "links": {"self": "/forest/StrPKRelation/hello%2Fother%2Fpeople"},
                        "type": "StrPKRelation",
                        "attributes": {"pk": "hello/other/people", "name": "hello other people"},
                    }
                ],
            },
        )
