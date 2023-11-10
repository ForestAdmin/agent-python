from django.apps import apps
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.interface import BaseDjangoDatasource


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(self) -> None:
        super().__init__()
        self._create_collections()

    def _create_collections(self):
        models = apps.get_models(include_auto_created=True)
        for model in models:
            collection = DjangoCollection(self, model)
            self.add_collection(collection)
