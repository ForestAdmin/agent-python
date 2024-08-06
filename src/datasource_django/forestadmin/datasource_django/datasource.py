from django.apps import apps
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.interface import BaseDjangoDatasource


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(self, support_polymorphic_relations: bool = False) -> None:
        super().__init__()
        self.support_polymorphic_relations = support_polymorphic_relations
        self._create_collections()

    def _create_collections(self):
        models = apps.get_models(include_auto_created=True)
        for model in models:
            if model._meta.proxy is False:
                collection = DjangoCollection(self, model, self.support_polymorphic_relations)
                self.add_collection(collection)
