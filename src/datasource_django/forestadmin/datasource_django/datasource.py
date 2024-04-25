from importlib.metadata import version
from typing import Any, Dict

from django.apps import apps
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.interface import BaseDjangoDatasource


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(self):
        super().__init__()
        self._create_collections()

    @classmethod
    def mk_meta_entry(cls) -> Dict[str, Any]:
        return {
            "name": "DjangoDatasource",
            "version": version("forestadmin-agent-django").replace("b", "-beta."),
            "django_version": version("django").replace("b", "-beta."),
        }

    def _create_collections(self):
        models = apps.get_models(include_auto_created=True)
        for model in models:
            if model._meta.proxy is False:
                collection = DjangoCollection(self, model)
                self.add_collection(collection)
