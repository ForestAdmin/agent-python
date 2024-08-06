from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from django.apps import apps
from django.db import models
from forestadmin.datasource_django.utils.model_introspection import DjangoCollectionFactory, FieldFactory
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from test_app.models import Book, Person, Rating


class TestDjangoFieldFactory(TestCase):
    def test_build_should_build_string_field(self):
        """basics"""
        field = models.TextField(null=True)
        field_schema = FieldFactory.build(field, None)
        self.assertEqual(field_schema["column_type"], PrimitiveType.STRING)
        self.assertEqual(field_schema["is_primary_key"], False)
        self.assertEqual(field_schema["is_read_only"], False)
        self.assertEqual(field_schema["default_value"], None)
        self.assertEqual(field_schema["validations"], [])
        self.assertEqual(field_schema["enum_values"], None)
        self.assertEqual(field_schema["type"], FieldType.COLUMN)

    def test_build_should_build_with_default_value(self):
        """default values"""
        field = models.TextField(null=True, default="my default value")
        field_schema = FieldFactory.build(field, None)
        self.assertEqual(field_schema["default_value"], "my default value")

    def test_build_should_ignore_dynamic_default_value(self):
        """default values"""
        field = models.TextField(null=True, default=lambda: "my default value")
        field_schema = FieldFactory.build(field, None)
        self.assertEqual(field_schema["default_value"], None)

    def test_build_should_handle_primary_key(self):
        """primary key"""
        field = models.IntegerField(primary_key=True)
        field.model = None
        field_schema = FieldFactory.build(field, None)
        self.assertEqual(field_schema["is_primary_key"], True)

    def test_build_should_handle_enums(self):
        """enums"""
        choices = [
            (1, "TOP"),
            (2, "MIDDLE"),
            (3, "BOTTOM"),
        ]
        field = models.IntegerField(choices=choices)
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["enum_values"], ["1", "2", "3"])
        self.assertEqual(field_schema["column_type"], PrimitiveType.ENUM)

    def test_build_should_use_str_on_enum_values_when_value_is_not_json_serializable(self):
        """enums"""
        now = datetime.now()
        choices = [
            (datetime(1916, 1, 1, 1, 1, 1), "WW1"),
            (datetime(1941, 2, 2, 2, 2, 2), "WW2"),
            (now, "NOW"),
        ]
        field = models.DateField(choices=choices)
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["enum_values"], ["1916-01-01 01:01:01", "1941-02-02 02:02:02", str(now)])
        self.assertEqual(field_schema["column_type"], PrimitiveType.ENUM)

    def test_build_should_handle_read_only_for_auto_increment_pk(self):
        """readonly"""
        field = models.AutoField(primary_key=True)
        field.model = None
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["is_read_only"], True)

    def test_build_should_handle_read_only_for_date_auto_now(self):
        """readonly"""
        field = models.DateField(auto_now=True)
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["is_read_only"], True)

    def test_build_should_handle_read_only_field_is_editable(self):
        """readonly"""
        field = models.CharField(max_length=254, editable=False)
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["is_read_only"], True)

    def test_build_should_handle_read_only_field_is_not_editable(self):
        """readonly"""
        field = models.CharField(max_length=254, editable=True)
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["is_read_only"], False)

    def test_build_should_handle_present_validator(self):
        """validator"""
        field = models.DateField()
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(field_schema["validations"], [{"operator": Operator.PRESENT}])

    def test_build_should_handle_max_len_validator_for_max_length_attr(self):
        """validator"""
        field = models.CharField(max_length=254)
        field_schema = FieldFactory.build(field, None)

        self.assertEqual(
            field_schema["validations"],
            [{"operator": Operator.PRESENT}, {"operator": Operator.SHORTER_THAN, "value": 254}],
        )

    def test_build_should_correctly_introspect_uuid(self):
        field = models.UUIDField()
        field_schema = FieldFactory.build(field, None)
        self.assertEqual(field_schema["column_type"], PrimitiveType.UUID)
        self.assertEqual(
            field_schema["filter_operators"],
            {
                Operator.BLANK,
                Operator.EQUAL,
                Operator.MISSING,
                Operator.NOT_EQUAL,
                Operator.PRESENT,
                Operator.CONTAINS,
                Operator.ENDS_WITH,
                Operator.STARTS_WITH,
                Operator.IN,
                Operator.NOT_IN,
            },
        )

    def test_introspected_field_should_respect_django_capabilities(self):
        field = models.TextField()
        field_schema = FieldFactory.build(field, None)
        self.assertEqual(field_schema["column_type"], PrimitiveType.STRING)
        self.assertEqual(
            field_schema["filter_operators"],
            {
                Operator.BLANK,
                Operator.EQUAL,
                Operator.MISSING,
                Operator.NOT_EQUAL,
                Operator.PRESENT,
                Operator.CONTAINS,
                Operator.NOT_CONTAINS,
                Operator.ENDS_WITH,
                Operator.STARTS_WITH,
                Operator.IN,
                Operator.NOT_IN,
            },
        )
        self.assertNotIn(Operator.SHORTER_THAN, field_schema["filter_operators"])
        self.assertNotIn(Operator.LIKE, field_schema["filter_operators"])
        self.assertNotIn(Operator.LONGER_THAN, field_schema["filter_operators"])


class TestDjangoCollectionFactory(TestCase):
    @staticmethod
    def build_model_class(name, attrs):
        return type(
            name,
            (models.Model,),
            {"__module__": "test_app", **attrs},
        )

    @classmethod
    def setUpClass(cls) -> None:
        cls.places_model = TestDjangoCollectionFactory.build_model_class(
            "Place",
            {
                "place_pk": models.BigAutoField(primary_key=True),
                "name": models.CharField(max_length=254),
            },
        )
        cls.restaurant_model = TestDjangoCollectionFactory.build_model_class(
            "Restaurant",
            {
                "restaurant_pk": models.BigAutoField(primary_key=True),
                "name": models.CharField(max_length=254),
                "place": models.OneToOneField("Place", related_name="restaurant", on_delete=models.CASCADE),
            },
        )
        cls.field_only_model = TestDjangoCollectionFactory.build_model_class(
            "FieldOnly", {"name": models.CharField(max_length=254)}
        )
        super().setUpClass()

    def test_build_should_call_field_factory_for_non_relational_fields(self):
        with patch(
            "forestadmin.datasource_django.utils.model_introspection.FieldFactory.build", wraps=FieldFactory.build
        ) as spy_field_factory_build:
            schema = DjangoCollectionFactory.build(self.field_only_model, False)
            for name, field_schema in schema["fields"].items():
                spy_field_factory_build.assert_any_call(
                    self.field_only_model._meta.get_field(name), self.field_only_model
                )
        self.assertEqual(set(schema["fields"].keys()), set(["id", "name"]))

    def test_build_should_handle_one_to_one_relations(self):
        places_schema = DjangoCollectionFactory.build(self.places_model, False)
        restaurant_schema = DjangoCollectionFactory.build(self.restaurant_model, False)

        self.assertIn("place", restaurant_schema["fields"].keys())
        self.assertIn("restaurant", places_schema["fields"].keys())

        self.assertEqual(
            restaurant_schema["fields"]["place"],
            {
                "foreign_collection": "test_app_place",
                "foreign_key": "place_id",
                "foreign_key_target": "place_pk",
                "type": FieldType.MANY_TO_ONE,
            },
        )
        self.assertEqual(
            places_schema["fields"]["restaurant"],
            {
                "foreign_collection": "test_app_restaurant",
                "origin_key": "place_id",
                "origin_key_target": "place_pk",
                "type": FieldType.ONE_TO_ONE,
            },
        )

    def test_build_should_handle_many_to_many_relations(self):
        user_model = apps.get_model("auth", "user")
        group_model = apps.get_model("auth", "group")

        user_schema = DjangoCollectionFactory.build(user_model, False)
        group_schema = DjangoCollectionFactory.build(group_model, False)

        self.assertEqual(
            user_schema["fields"]["groups"],
            {
                "type": FieldType.MANY_TO_MANY,
                "foreign_collection": "auth_group",
                "foreign_relation": None,
                "through_collection": "auth_user_groups",
                "origin_key": "user_id",
                "origin_key_target": "id",
                "foreign_key": "group_id",
                "foreign_key_target": "id",
            },
        )

        self.assertEqual(
            group_schema["fields"]["user"],
            {
                "type": FieldType.MANY_TO_MANY,
                "foreign_collection": "auth_user",
                "through_collection": "auth_user_groups",
                "foreign_relation": None,
                "foreign_key": "user_id",
                "foreign_key_target": "id",
                "origin_key": "group_id",
                "origin_key_target": "id",
            },
        )

    def test_build_should_handle_many_to_one_relations(self):
        user_groups_model = apps.get_model("auth", "user_groups")

        user_groups_schema = DjangoCollectionFactory.build(user_groups_model, False)

        self.assertEqual(
            user_groups_schema["fields"]["group"],
            {
                "foreign_collection": "auth_group",
                "foreign_key": "group_id",
                "foreign_key_target": "id",
                "type": FieldType.MANY_TO_ONE,
            },
        )

    def test_build_should_handle_one_to_many_relations(self):
        person_schema = DjangoCollectionFactory.build(Person, False)

        self.assertEqual(
            person_schema["fields"]["books_author"],
            {
                "foreign_collection": "test_app_book",
                "origin_key": "author_id",
                "origin_key_target": "person_pk",
                "type": FieldType.ONE_TO_MANY,
            },
        )

    def test_build_should_handle_also_generate_foreign_key_fields_next_to_relations(self):
        book_schema = DjangoCollectionFactory.build(Book, False)

        self.assertEqual(book_schema["fields"]["author_id"]["validations"], [])
        self.assertEqual(book_schema["fields"]["author_id"]["column_type"], PrimitiveType.NUMBER)
        self.assertEqual(book_schema["fields"]["author_id"]["type"], FieldType.COLUMN)

    def test_build_should_handle_polymorphic_many_to_one(self):
        rating_schema = DjangoCollectionFactory.build(Rating, True)

        self.assertEqual(
            rating_schema["fields"]["content_object"],
            {
                "foreign_collections": ["test_app_book", "test_app_person"],
                "foreign_key": "content_id",
                "foreign_key_type_field": "content_type",
                "foreign_key_targets": {"test_app_book": "book_pk", "test_app_person": "person_pk"},
                "type": FieldType.POLYMORPHIC_MANY_TO_ONE,
            },
        )
        self.assertEqual(
            rating_schema["fields"]["content_type"],
            {
                "column_type": PrimitiveType.ENUM,
                "is_primary_key": False,
                "is_read_only": True,
                "default_value": None,
                "is_sortable": True,
                "validations": [],
                "filter_operators": {
                    Operator.NOT_EQUAL,
                    Operator.ENDS_WITH,
                    Operator.PRESENT,
                    Operator.BLANK,
                    Operator.EQUAL,
                    Operator.NOT_IN,
                    Operator.IN,
                    Operator.MISSING,
                    Operator.NOT_CONTAINS,
                    Operator.SHORTER_THAN,
                    Operator.STARTS_WITH,
                    Operator.CONTAINS,
                    Operator.LIKE,
                    Operator.LONGER_THAN,
                },
                "enum_values": ["test_app_book", "test_app_person"],
                "type": FieldType.COLUMN,
            },
        )

    def test_build_should_handle_polymorphic_one_to_many(self):
        book_schema = DjangoCollectionFactory.build(Book, True)

        self.assertEqual(
            book_schema["fields"]["ratings"],
            {
                "foreign_collection": "test_app_rating",
                "origin_key": "content_id",
                "origin_key_target": "book_pk",
                "origin_type_field": "content_type",
                "origin_type_value": "test_app_book",
                "type": FieldType.POLYMORPHIC_ONE_TO_MANY,
            },
        )

    def test_build_should_handle_polymorphic_one_to_one(self):
        book_schema = DjangoCollectionFactory.build(Book, True)

        self.assertEqual(
            book_schema["fields"]["tag"],
            {
                "foreign_collection": "test_app_tag",
                "origin_key": "content_id",
                "origin_key_target": "book_pk",
                "origin_type_field": "content_type",
                "origin_type_value": "test_app_book",
                "type": FieldType.POLYMORPHIC_ONE_TO_ONE,
            },
        )

    def test_build_should_log_when_polymorphism_support_is_disabled(self):
        with patch("forestadmin.datasource_django.utils.model_introspection.ForestLogger.log") as mock_logger_fn:
            rating_schema = DjangoCollectionFactory.build(Rating, False)
            mock_logger_fn.assert_called_once_with(
                "info",
                "Ignoring test_app_rating.content_object because polymorphic relation is not supported.",
            )
            self.assertEqual(mock_logger_fn.call_count, 1)
        self.assertNotIn("content_object", rating_schema["fields"].keys())

        with patch("forestadmin.datasource_django.utils.model_introspection.ForestLogger.log") as mock_logger_fn:
            rating_schema = DjangoCollectionFactory.build(Person, False)
            mock_logger_fn.assert_any_call(
                "info",
                "Ignoring test_app_person.ratings because polymorphic relation is not supported.",
            )
            mock_logger_fn.assert_any_call(
                "info",
                "Ignoring test_app_person.tag because polymorphic relation is not supported.",
            )
            self.assertEqual(mock_logger_fn.call_count, 2)
        self.assertNotIn("content_object", rating_schema["fields"].keys())
