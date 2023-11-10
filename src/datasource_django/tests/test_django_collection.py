from unittest.mock import Mock, patch

from django.test import TestCase
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.datasource import DjangoDatasource

from .test_project.test_app.models import Book


class TestDjangoCollection(TestCase):
    def setUp(self) -> None:
        self.datasource = Mock(DjangoDatasource)

    def test_creation_should_introspect_given_model(self):
        with patch(
            "forestadmin.datasource_django.collection.DjangoCollectionFactory.build",
            return_value={"actions": {}, "fields": {}, "searchable": False, "segments": []},
        ) as mock_factory_build:
            DjangoCollection(self.datasource, Book)
            mock_factory_build.assert_called_once_with(Book)

    def test_model_property_should_return_model_instance(self):
        collection = DjangoCollection(self.datasource, Book)
        self.assertEqual(collection.model, Book)
