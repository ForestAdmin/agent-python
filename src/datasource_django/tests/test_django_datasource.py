from unittest import TestCase
from unittest.mock import Mock, call, patch

from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.datasource import DjangoDatasource

mock_collection1 = Mock(DjangoCollection)
mock_collection1.name = "first"
mock_collection2 = Mock(DjangoCollection)
mock_collection2.name = "second"


class TestDjangoDatasource(TestCase):
    def test_creation_should_call_create_collections(self):
        with patch.object(DjangoDatasource, "_create_collections") as mock_create_collection:
            DjangoDatasource()
            mock_create_collection.assert_called_once()

    @patch(
        "forestadmin.datasource_django.datasource.apps.get_models", return_value=[mock_collection1, mock_collection2]
    )
    @patch("forestadmin.datasource_django.datasource.DjangoCollection", side_effect=lambda datasource, model: model)
    def test_create_collection_should_add_a_collection(self, mock_DjangoCollection: Mock, mock_get_models: Mock):
        with patch.object(DjangoDatasource, "_create_collections"):
            django_datasource = DjangoDatasource()

        django_datasource._create_collections()
        mock_get_models.assert_called_once_with(include_auto_created=True)
        mock_DjangoCollection.assert_has_calls(
            [
                call(django_datasource, mock_collection1),
                call(django_datasource, mock_collection2),
            ]
        )
        self.assertEqual(set(django_datasource.collections), set([mock_collection1, mock_collection2]))

    def test_django_datasource_should_find_all_models(self):
        datasource = DjangoDatasource()
        self.assertEqual(
            set([c.name for c in datasource.collections]),
            set(
                [
                    "Book",
                    "Person",
                    "Rating",
                    "Permission",
                    "Group_permissions",
                    "Group",
                    "User_groups",
                    "User_user_permissions",
                    "User",
                    "ContentType",
                ]
            ),
        )
