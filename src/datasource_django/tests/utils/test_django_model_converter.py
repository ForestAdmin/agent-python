from unittest import TestCase
from unittest.mock import patch

from django.apps import apps
from django.db import models
from forestadmin.datasource_django.utils.model_introspection import DjangoCollectionFactory, FieldFactory
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType


class TestDjangoFieldFactory(TestCase):
    def test_build_should_build_string_field(self):
        """basics"""
        field = models.TextField(null=True)
        field_schema = FieldFactory.build(field)
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
        field_schema = FieldFactory.build(field)
        self.assertEqual(field_schema["default_value"], "my default value")

    def test_build_should_ignore_dynamic_default_value(self):
        """default values"""
        field = models.TextField(null=True, default=lambda: "my default value")
        field_schema = FieldFactory.build(field)
        self.assertEqual(field_schema["default_value"], None)

    def test_build_should_handle_primary_key(self):
        """primary key"""
        field = models.IntegerField(primary_key=True)
        field_schema = FieldFactory.build(field)
        self.assertEqual(field_schema["is_primary_key"], True)

    def test_build_should_handle_enums(self):
        """enums"""
        choices = [
            (1, "TOP"),
            (2, "MIDDLE"),
            (3, "BOTTOM"),
        ]
        field = models.IntegerField(choices=choices)
        field_schema = FieldFactory.build(field)

        self.assertEqual(field_schema["enum_values"], [1, 2, 3])
        self.assertEqual(field_schema["column_type"], PrimitiveType.ENUM)

    def test_build_should_handle_read_only_for_auto_increment_pk(self):
        """readonly"""
        field = models.AutoField(primary_key=True)
        field_schema = FieldFactory.build(field)

        self.assertEqual(field_schema["is_read_only"], True)

    def test_build_should_handle_read_only_for_date_auto_now(self):
        """readonly"""
        field = models.DateField(auto_now=True)
        field_schema = FieldFactory.build(field)

        self.assertEqual(field_schema["is_read_only"], True)

    def test_build_should_handle_present_validator(self):
        """validator"""
        field = models.DateField()
        field_schema = FieldFactory.build(field)

        self.assertEqual(field_schema["validations"], [{"operator": Operator.PRESENT}])

    def test_build_should_handle_max_len_validator_for_max_length_attr(self):
        """validator"""
        field = models.CharField(max_length=254)
        field_schema = FieldFactory.build(field)

        self.assertEqual(
            field_schema["validations"],
            [{"operator": Operator.PRESENT}, {"operator": Operator.SHORTER_THAN, "value": 254}],
        )


class TestDjangoCollectionFactory(TestCase):
    @staticmethod
    def build_model_class(name, attrs):
        return type(
            name,
            (models.Model,),
            {"__module__": "tests.test_project.test_app.models", **attrs},
        )

    @classmethod
    def setUpClass(cls) -> None:
        cls.places_model = TestDjangoCollectionFactory.build_model_class(
            "Place", {"name": models.CharField(max_length=254)}
        )
        cls.restaurant_model = TestDjangoCollectionFactory.build_model_class(
            "Restaurant",
            {
                "name": models.CharField(max_length=254),
                "place": models.OneToOneField("Place", related_name="restaurant", on_delete=models.CASCADE),
            },
        )
        cls.field_only_model = TestDjangoCollectionFactory.build_model_class(
            "FieldOnly", {"name": models.CharField(max_length=254)}
        )
        cls.author_model = TestDjangoCollectionFactory.build_model_class("author", {})
        cls.movie_model = TestDjangoCollectionFactory.build_model_class(
            "movie", {"author": models.ForeignKey("author", on_delete=models.CASCADE, related_name="movies")}
        )

    def test_build_should_call_field_factory_for_non_relational_fields(self):
        with patch(
            "forestadmin.datasource_django.utils.model_introspection.FieldFactory.build", wraps=FieldFactory.build
        ) as spy_field_factory_build:
            schema = DjangoCollectionFactory.build(self.field_only_model)
            for name, field_schema in schema["fields"].items():
                spy_field_factory_build.assert_any_call(self.field_only_model._meta.get_field(name))
        self.assertEqual(set(schema["fields"].keys()), set(["id", "name"]))

    def test_build_should_handle_one_to_one_relations(self):
        places_schema = DjangoCollectionFactory.build(self.places_model)
        restaurant_schema = DjangoCollectionFactory.build(self.restaurant_model)

        self.assertIn("place", restaurant_schema["fields"].keys())
        self.assertIn("restaurant", places_schema["fields"].keys())

        self.assertEqual(
            restaurant_schema["fields"]["place"],
            {
                "foreign_collection": "Place",
                "foreign_key": "place_id",
                "foreign_key_target": "id",
                "type": FieldType.MANY_TO_ONE,
            },
        )
        self.assertEqual(
            places_schema["fields"]["restaurant"],
            {
                "foreign_collection": "Restaurant",
                "origin_key": "place_id",
                "origin_key_target": "id",
                "type": FieldType.ONE_TO_ONE,
            },
        )

    def test_build_should_handle_many_to_many_relations(self):
        user_model = apps.get_model("auth", "user")
        group_model = apps.get_model("auth", "group")

        user_schema = DjangoCollectionFactory.build(user_model)
        group_schema = DjangoCollectionFactory.build(group_model)

        self.assertEqual(
            user_schema["fields"]["groups"],
            {
                "type": FieldType.MANY_TO_MANY,
                "foreign_collection": "Group",
                "foreign_relation": None,
                "through_collection": "User_groups",
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
                "foreign_collection": "User",
                "through_collection": "User_groups",
                "foreign_relation": None,
                "foreign_key": "user_id",
                "foreign_key_target": "id",
                "origin_key": "group_id",
                "origin_key_target": "id",
            },
        )

    def test_build_should_handle_many_to_one_relations(self):
        user_groups_model = apps.get_model("auth", "user_groups")

        user_groups_schema = DjangoCollectionFactory.build(user_groups_model)

        self.assertEqual(
            user_groups_schema["fields"]["group"],
            {
                "foreign_collection": "Group",
                "foreign_key": "group_id",
                "foreign_key_target": "id",
                "type": FieldType.MANY_TO_ONE,
            },
        )

    def test_build_should_handle_one_to_many_relations(self):
        author_schema = DjangoCollectionFactory.build(self.author_model)

        self.assertEqual(
            author_schema["fields"]["movies"],
            {
                "foreign_collection": "movie",
                "origin_key": "author_id",
                "origin_key_target": "id",
                "type": FieldType.ONE_TO_MANY,
            },
        )

    def test_build_should_handle_also_generate_foreign_key_fields_next_to_relations(self):
        movie_schema = DjangoCollectionFactory.build(self.movie_model)

        self.assertEqual(movie_schema["fields"]["author_id"]["validations"], [{"operator": Operator.PRESENT}])
        self.assertEqual(movie_schema["fields"]["author_id"]["column_type"], PrimitiveType.NUMBER)
        self.assertEqual(movie_schema["fields"]["author_id"]["type"], FieldType.COLUMN)
