from django.apps import apps
from forestadmin.agent_toolkit.forest_logger import log_current_ram
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.interface import BaseDjangoDatasource
from memory_profiler import profile


class DjangoDatasource(BaseDjangoDatasource):
    def __init__(self) -> None:
        log_current_ram("before django datasource creation")

        super().__init__()
        self._create_collections()

    @profile
    def _create_collections(self):
        models = apps.get_models(include_auto_created=True)
        for model in models:
            if model._meta.proxy is False:
                collection = DjangoCollection(self, model)
                self.add_collection(collection)
