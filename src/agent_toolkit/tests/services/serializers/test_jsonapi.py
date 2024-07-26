from datetime import date, datetime, timezone
from typing import cast
from unittest import TestCase
from unittest.mock import patch

from forestadmin.agent_toolkit.services.serializers.json_api import (
    JsonApiException,
    JsonApiSerializer,
    _create_relationship,
    _map_attribute_to_marshmallow,
    create_json_api_schema,
    refresh_json_api_schema,
    schema_name,
)
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
    RelationAlias,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory


class TestJsonApi(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_person = Collection("Person", cls.datasource)
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

        cls.collection_profile = Collection("Profile", cls.datasource)
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

        cls.collection_order = Collection("Order", cls.datasource)
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

        cls.collection_order_products = Collection("OrderProducts", cls.datasource)
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

        cls.collection_product = Collection("Product", cls.datasource)
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

        cls.collection_picture = Collection("Picture", cls.datasource)
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

        cls.collection_comment = Collection("Comment", cls.datasource)
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

        cls.datasource.add_collection(cls.collection_order)
        cls.datasource.add_collection(cls.collection_order_products)
        cls.datasource.add_collection(cls.collection_product)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_profile)
        cls.datasource.add_collection(cls.collection_picture)
        cls.datasource.add_collection(cls.collection_comment)


class TestJsonApiSchemaCreation(TestJsonApi):
    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_should_create_and_register_schema(self):
        create_json_api_schema(self.collection_product)
        self.assertIn(schema_name(self.collection_product), JsonApiSerializer.schema.keys())
        schema = JsonApiSerializer.schema[schema_name(self.collection_product)]
        self.assertIsNotNone(schema)
        self.assertEqual(schema.Meta.type_, self.collection_product.name)
        self.assertEqual(schema.Meta.fcollection, self.collection_product)
        self.assertEqual(schema.Meta.fcollection, self.collection_product)
        self.assertEqual(schema.Meta.self_url, "/forest/Product/{product_id}")

        for name, field_schema in self.collection_product.schema["fields"].items():
            if name == "pk":
                self.assertIsNotNone(schema.attributes["product_schema"].get("id"))
                # pk is name as original and also "id"
            self.assertIsNotNone(schema.attributes["product_schema"].get(name))

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_should_raise_if_schema_already_exists(self):
        create_json_api_schema(self.collection_product)

        self.assertRaisesRegex(
            JsonApiException,
            r"The schema has already been created for this collection",
            create_json_api_schema,
            self.collection_product,
        )

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_refresh_json_api_schema_should_replace_current_schema(self):
        with patch.object(JsonApiSerializer, "schema", dict()):
            create_json_api_schema(self.collection_product)
            existing_schema = JsonApiSerializer.schema[schema_name(self.collection_product)]
            refresh_json_api_schema(self.collection_product)
            replaced_schema = JsonApiSerializer.schema[schema_name(self.collection_product)]
            self.assertNotEqual(existing_schema, replaced_schema)

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_refresh_json_api_schema_should_raise_if_schema_does_not_exists(self):
        self.assertRaisesRegex(
            JsonApiException, r"The schema doesn't exist", refresh_json_api_schema, self.collection_product
        )

    def test_map_attribute_to_marshmallow_should_correctly_handled_allow_none(self):
        res = _map_attribute_to_marshmallow(
            Column(
                column_type=PrimitiveType.STRING,
                type=FieldType.COLUMN,
                is_sortable=True,
                default_value=None,
                enum_values=None,
                is_primary_key=False,
                filter_operators=set([Operator.EQUAL, Operator.IN]),
                is_read_only=False,
                validations=[],
            ),
        )
        self.assertEqual(res.allow_none, True)

        res = _map_attribute_to_marshmallow(
            Column(
                column_type=PrimitiveType.STRING,
                type=FieldType.COLUMN,
                is_sortable=True,
                default_value=None,
                enum_values=None,
                is_primary_key=False,
                filter_operators=set([Operator.EQUAL, Operator.IN]),
                is_read_only=True,
                validations=[],
            ),
        )
        self.assertEqual(res.allow_none, True)

        res = _map_attribute_to_marshmallow(
            Column(
                column_type=PrimitiveType.STRING,
                type=FieldType.COLUMN,
                is_sortable=True,
                default_value=None,
                enum_values=None,
                is_primary_key=False,
                filter_operators=set([Operator.EQUAL, Operator.IN]),
                is_read_only=False,
                validations=[{"operator": Operator.PRESENT}],
            ),
        )
        self.assertEqual(res.allow_none, False)

    def test_create_relationship_should_handle_many_to_one(self):
        ret = _create_relationship(
            self.collection_order, "customer", cast(RelationAlias, self.collection_order.schema["fields"]["customer"])
        )

        self.assertEqual(ret.collection, self.collection_order)
        self.assertEqual(ret.related_collection_name, "Person")
        self.assertEqual(ret.forest_is_polymorphic, False)
        self.assertEqual(ret.id_field, "person_pk")
        self.assertEqual(ret.many, False)
        self.assertEqual(ret.type_, "Person")
        self.assertEqual(ret._Relationship__schema, "Person_schema")

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_relationship_should_handle_many_to_many(self):
        create_json_api_schema(self.collection_product)
        ret = _create_relationship(
            self.collection_order, "products", cast(RelationAlias, self.collection_order.schema["fields"]["products"])
        )

        self.assertEqual(ret.collection, self.collection_order)
        self.assertEqual(ret.related_collection_name, "Product")
        self.assertEqual(ret.forest_is_polymorphic, False)
        self.assertEqual(ret.id_field, "product_pk")  # it should be pk; but jsonapi always use id
        self.assertEqual(ret.many, True)
        self.assertEqual(ret.type_, "Product")
        self.assertEqual(ret._Relationship__schema, "Product_schema")

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_relationship_should_handle_one_to_many(self):
        create_json_api_schema(self.collection_order)
        ret = _create_relationship(
            self.collection_person, "orders", cast(RelationAlias, self.collection_person.schema["fields"]["orders"])
        )

        self.assertEqual(ret.collection, self.collection_person)
        self.assertEqual(ret.related_collection_name, "Order")
        self.assertEqual(ret.forest_is_polymorphic, False)
        self.assertEqual(ret.id_field, "order_pk")
        self.assertEqual(ret.many, True)
        self.assertEqual(ret.type_, "Order")
        self.assertEqual(ret._Relationship__schema, "Order_schema")

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_relationship_should_handle_one_to_one(self):
        create_json_api_schema(self.collection_profile)
        ret = _create_relationship(
            self.collection_person, "profile", cast(RelationAlias, self.collection_person.schema["fields"]["profile"])
        )

        self.assertEqual(ret.collection, self.collection_person)
        self.assertEqual(ret.related_collection_name, "Profile")
        self.assertEqual(ret.forest_is_polymorphic, False)
        self.assertEqual(ret.id_field, "profile_pk")
        self.assertEqual(ret.many, False)
        self.assertEqual(ret.type_, "Profile")
        self.assertEqual(ret._Relationship__schema, "Profile_schema")

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_relationship_should_handle_polymorphic_many_to_one(self):
        create_json_api_schema(self.collection_profile)
        create_json_api_schema(self.collection_product)
        ret = _create_relationship(
            self.collection_picture,
            "target_object",
            cast(RelationAlias, self.collection_picture.schema["fields"]["target_object"]),
        )

        self.assertEqual(ret.collection, self.collection_picture)
        self.assertEqual(ret.related_collection_name, ["Product", "Profile"])
        self.assertEqual(ret.forest_is_polymorphic, True)
        # self.assertEqual(ret.id_field, "id")
        self.assertEqual(ret.many, False)
        self.assertEqual(ret.forest_relation, self.collection_picture.schema["fields"]["target_object"])
        self.assertEqual(ret.type_, ["Product", "Profile"])
        self.assertEqual(ret._Relationship__schema, "['Product', 'Profile']_schema")

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_relationship_should_handle_polymorphic_one_to_one(self):
        create_json_api_schema(self.collection_picture)
        create_json_api_schema(self.collection_product)
        ret = _create_relationship(
            self.collection_profile,
            "picture",
            cast(RelationAlias, self.collection_profile.schema["fields"]["picture"]),
        )

        self.assertEqual(ret.collection, self.collection_profile)
        self.assertEqual(ret.related_collection_name, "Picture")
        self.assertEqual(ret.forest_is_polymorphic, False)
        self.assertEqual(ret.id_field, "picture_pk")
        self.assertEqual(ret.many, False)
        self.assertEqual(ret.type_, "Picture")
        self.assertEqual(ret._Relationship__schema, "Picture_schema")

    @patch.object(JsonApiSerializer, "schema", dict())
    def test_create_relationship_should_handle_polymorphic_one_to_many(self):
        create_json_api_schema(self.collection_picture)
        create_json_api_schema(self.collection_product)
        ret = _create_relationship(
            self.collection_profile,
            "comments",
            cast(RelationAlias, self.collection_profile.schema["fields"]["comments"]),
        )

        self.assertEqual(ret.collection, self.collection_profile)
        self.assertEqual(ret.related_collection_name, "Comment")
        self.assertEqual(ret.forest_is_polymorphic, False)
        self.assertEqual(ret.id_field, "comment_pk")
        self.assertEqual(ret.many, True)
        self.assertEqual(ret.type_, "Comment")
        self.assertEqual(ret._Relationship__schema, "Comment_schema")


class TestJsonApiSchemaDump(TestJsonApi):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for collection in cls.datasource.collections:
            create_json_api_schema(collection)

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

    @classmethod
    def tearDownClass(cls) -> None:
        JsonApiSerializer.schema = dict()
        return super().tearDownClass()

    def test_should_correctly_dump_attributes_according_to_projection(self):
        projection = ProjectionFactory.all(self.collection_product, allow_nested=False)
        schema = JsonApiSerializer.get(self.collection_product)(projections=projection)

        dumped = schema.dump(self.product_records, many=True)
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

    def test_should_correctly_dump_int_or_float_from_string_value(self):
        projection = ProjectionFactory.all(self.collection_product, allow_nested=False)
        schema = JsonApiSerializer.get(self.collection_product)(projections=projection)

        records = [
            {**self.product_records[0]},
            {**self.product_records[1]},
        ]
        records[0]["price"] = "2.23"
        records[1]["price"] = "10"

        dumped = schema.dump(records, many=True)
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
        schema = JsonApiSerializer.get(self.collection_order)(
            projections=Projection("order_pk", "customer_id", "customer:person_pk", "customer:first_name")
        )

        record = {**self.order_records[0]}
        record["customer"] = {**self.person_records[0]}
        record["customer_id"] = record["customer"]["person_pk"]

        dumped = schema.dump(record, many=False)
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
                        "id": "12",
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
        schema = JsonApiSerializer.get(self.collection_order)(
            projections=Projection(
                "order_pk",
                "customer_id",
                "products:label",
                "products:price",
                "products:product_pk",
                "order_products:product_id",
            )
        )

        record = {**self.order_records[0]}
        record["customer_id"] = self.person_records[0]["person_pk"]
        record["products"] = None
        record["order_products"] = None

        dumped = schema.dump(record, many=False)
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
                                    "href": "/forest/Order/825dfdf9-1339-4373-af7b-261d99b09622/relationships/order_products"
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
        schema = JsonApiSerializer.get(self.collection_comment)(
            projections=Projection("comment_pk", "comment", "target_id", "target_type", "target_object:*")
        )
        dumped = schema.dump(self.comments_records, many=True)
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
                                        "href": "/forest/Comment/0b622590-c823-4d2f-84e6-bbbdd31c8af8/relationships/target_object"
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
                                        "href": "/forest/Comment/60908a3e-97d7-4518-a724-17359e05c9e2/relationships/target_object"
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
                                        "href": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af/relationships/orders"
                                    }
                                }
                            },
                            "picture": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af/relationships/picture"
                                    }
                                }
                            },
                            "comments": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Product/8f6834d7-845f-421c-ac8a-76fd9b5895af/relationships/comments"
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
                                        "href": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf/relationships/person"
                                    }
                                }
                            },
                            "picture": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf/relationships/picture"
                                    }
                                }
                            },
                            "comments": {
                                "links": {
                                    "related": {
                                        "href": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf/relationships/comments"
                                    }
                                }
                            },
                        },
                        "links": {"self": "/forest/Profile/913b45d2-712e-4f93-a1e8-79519ef756bf"},
                    },
                ],
            },
        )


class TestJsonApiSchemaLoad(TestJsonApi):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for collection in cls.datasource.collections:
            create_json_api_schema(collection)

    @classmethod
    def tearDownClass(cls) -> None:
        JsonApiSerializer.schema = dict()
        return super().tearDownClass()

    def test_should_correctly_load_attributes(self):
        schema = JsonApiSerializer.get(self.collection_product)()

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

        data = schema.load(request_body)
        self.assertEqual(
            data,
            {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "price": 2.23,
                "label": "strawberries",
                "date_online": datetime(2023, 10, 10, 10, 10, 10, tzinfo=timezone.utc),
            },
        )
        # as this line https://github.com/ForestAdmin/agent-python/blob/main/src/agent_toolkit/forestadmin/agent_toolkit/resources/collections/crud.py#L245C1-L246C1
        # it seems normal json api doesn't load the primary key in another field than id

    def test_should_correctly_load_int_or_float_from_string_value(self):
        schema = JsonApiSerializer.get(self.collection_product)()

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {
                    "price": "2.23",
                },
                "type": "Product",
            }
        }

        data = schema.load(request_body)
        self.assertEqual(
            data,
            {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "price": 2.23,
            },
        )

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {
                    "price": "10",
                },
                "type": "Product",
            }
        }

        data = schema.load(request_body)
        self.assertEqual(
            data,
            {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "price": 10,
            },
        )

    def test_should_correctly_load_many_to_one_relationship(self):
        schema = JsonApiSerializer.get(self.collection_order)()

        request_body = {
            "data": {
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
                "attributes": {},
                "type": "Orders",
                "relationships": {
                    "customer": {"data": {"id": "12", "type": "Persons"}},
                    "products": {"data": []},
                    "order_products": {"data": []},
                },
            }
        }
        data = schema.load(request_body)
        self.assertEqual(
            data,
            {
                "customer": 12,
                "products": [],
                "order_products": [],
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
            },
        )

    def test_should_correctly_load_to_many_relations(self):
        schema = JsonApiSerializer.get(self.collection_order)()

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
                            {"type": "OrderProducts", "id": "833a6308-da81-4363-9448-d101eb593d94"},
                            {"type": "OrderProducts", "id": "9f9348fe-3d2d-43be-b0be-ff58313b137e"},
                        ]
                    },
                },
            }
        }
        data = schema.load(request_body)
        self.assertEqual(
            data,
            {
                "products": ["0086ebe0-3452-4779-91de-26d14850998c", "68dcab0f-2dec-468f-8ebd-ff2752d24b81"],
                "order_products": ["833a6308-da81-4363-9448-d101eb593d94", "9f9348fe-3d2d-43be-b0be-ff58313b137e"],
                "id": "43661dae-97c3-4ea9-bd43-a6d8ac3f4ca7",
            },
        )

    def test_should_correctly_load_polymorphic_many_to_one_relation(self):
        schema = JsonApiSerializer.get(self.collection_comment)()
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

        data = schema.load(request_body)
        self.assertEqual(
            data,
            {
                "target_id": "1806bdb7-5db4-46a1-acca-9a00f8a670dd",
                "target_type": "Product",
                "comment": "I like it a lot.",
            },
        )
