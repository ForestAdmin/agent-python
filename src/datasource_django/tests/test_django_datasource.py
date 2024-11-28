import asyncio
from unittest.mock import Mock, call, patch

from django.test import SimpleTestCase, TestCase
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.datasource_django.exception import DjangoDatasourceException

mock_collection1 = Mock(DjangoCollection)
mock_collection1.name = "first"
mock_collection1._meta = Mock()
mock_collection1._meta.proxy = False
mock_collection2 = Mock(DjangoCollection)
mock_collection2.name = "second"
mock_collection2._meta = Mock()
mock_collection2._meta.proxy = False


class TestDjangoDatasource(TestCase):
    def test_creation_should_call_create_collections(self):
        with patch.object(DjangoDatasource, "_create_collections") as mock_create_collection:
            DjangoDatasource()
            mock_create_collection.assert_called_once()

    @patch(
        "forestadmin.datasource_django.datasource.apps.get_models", return_value=[mock_collection1, mock_collection2]
    )
    @patch(
        "forestadmin.datasource_django.datasource.DjangoCollection",
        side_effect=lambda datasource, model, support_polymorphic_relations: model,
    )
    def test_create_collection_should_add_a_collection(self, mock_DjangoCollection: Mock, mock_get_models: Mock):
        with patch.object(DjangoDatasource, "_create_collections"):
            django_datasource = DjangoDatasource()

        django_datasource._create_collections()
        mock_get_models.assert_called_once_with(include_auto_created=True)
        mock_DjangoCollection.assert_has_calls(
            [
                call(django_datasource, mock_collection1, False),
                call(django_datasource, mock_collection2, False),
            ]
        )
        self.assertEqual(set(django_datasource.collections), set([mock_collection1, mock_collection2]))

    def test_django_datasource_should_find_all_models(self):
        datasource = DjangoDatasource()
        self.assertEqual(
            sorted([c.name for c in datasource.collections]),
            sorted(
                [
                    "test_app_book",
                    "test_app_person",
                    "test_app_rating",
                    "test_app_tag",
                    "auth_permission",
                    "auth_group_permissions",
                    "auth_group",
                    "auth_user_groups",
                    "auth_user_user_permissions",
                    "auth_user",
                    "django_content_type",
                ]
            ),
        )

    def test_django_datasource_should_ignore_proxy_models(self):
        """ignoring proxy models means no collections added twice or more"""
        datasource = DjangoDatasource()
        self.assertEqual(len([c.name for c in datasource.collections if c.name == "auth_user"]), 1)


class TestDjangoDatasourceConnectionQueryCreation(SimpleTestCase):
    def test_should_not_create_native_query_connection_if_no_params(self):
        ds = DjangoDatasource()
        self.assertEqual(ds.get_native_query_connections(), [])

    def test_should_create_native_query_connection_to_default_if_string_is_set(self):
        ds = DjangoDatasource(live_query_connection="django")
        self.assertEqual(ds.get_native_query_connections(), ["django"])
        self.assertEqual(ds._django_live_query_connections["django"], "default")

    def test_should_log_when_creating_connection_with_string_param_and_multiple_databases_are_set_up(self):
        with patch("forestadmin.datasource_django.datasource.ForestLogger.log") as log_fn:
            DjangoDatasource(live_query_connection="django")
            # TODO: adapt error message
            log_fn.assert_any_call(
                "info",
                "You enabled live query as django for django 'default' database. "
                "To use it over multiple databases, read the related documentation here: http://link.",
            )

    def test_should_raise_if_connection_query_target_non_existent_database(self):
        self.assertRaisesRegex(
            DjangoDatasourceException,
            r"Connection to database 'plouf' for alias 'plif' is not found in django databases\. "
            r"Existing connections are default,other",
            DjangoDatasource,
            live_query_connection={"django": "default", "plif": "plouf"},
        )


class TestDjangoDatasourceNativeQueryExecution(TestCase):
    fixtures = ["person.json", "book.json", "rating.json", "tag.json"]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.loop = asyncio.new_event_loop()
        cls.dj_datasource = DjangoDatasource(live_query_connection={"django": "default", "other": "other"})

    def test_should_raise_if_connection_is_not_known_by_datasource(self):
        self.assertRaisesRegex(
            DjangoDatasourceException,
            r"Native query connection 'foo' is not known by DjangoDatasource.",
            self.loop.run_until_complete,
            self.dj_datasource.execute_native_query("foo", "select * from blabla", {}),
        )

    async def test_should_correctly_execute_query(self):
        result = await self.dj_datasource.execute_native_query(
            "django", "select * from test_app_person order by person_pk;", {}
        )
        self.assertEqual(
            result,
            [
                {
                    "person_pk": 1,
                    "first_name": "Isaac",
                    "last_name": "Asimov",
                    "birth_date": "1920-02-01",
                    "auth_user_id": None,
                },
                {
                    "person_pk": 2,
                    "first_name": "J.K.",
                    "last_name": "Rowling",
                    "birth_date": "1965-07-31",
                    "auth_user_id": None,
                },
            ],
        )

    async def test_should_correctly_execute_query_with_formatting(self):
        result = await self.dj_datasource.execute_native_query(
            "django",
            "select * from test_app_person where first_name = %(first_name)s order by person_pk;",
            {"first_name": "Isaac"},
        )
        self.assertEqual(
            result,
            [
                {
                    "person_pk": 1,
                    "first_name": "Isaac",
                    "last_name": "Asimov",
                    "birth_date": "1920-02-01",
                    "auth_user_id": None,
                },
            ],
        )

    async def test_should_correctly_execute_query_with_percent(self):
        result = await self.dj_datasource.execute_native_query(
            "django",
            "select * from test_app_person where first_name like 'Is\\%' order by person_pk;",
            {},
        )
        self.assertEqual(
            result,
            [
                {
                    "person_pk": 1,
                    "first_name": "Isaac",
                    "last_name": "Asimov",
                    "birth_date": "1920-02-01",
                    "auth_user_id": None,
                },
            ],
        )

    def test_should_correctly_raise_exception_during_sql_error(self):
        self.assertRaisesRegex(
            DjangoDatasourceException,
            r"no such table: blabla",
            self.loop.run_until_complete,
            self.dj_datasource.execute_native_query("django", "select * from blabla", {}),
        )
