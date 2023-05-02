from forestadmin.agent_toolkit.services.serializers.json_api import create_json_api_schema
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection
from forestadmin.datasource_toolkit.decorators.datasource import CustomizedDatasource


class DatasourceCustomizer:
    def __init__(self) -> None:
        self.composite_datasource: Datasource = Datasource()

    def add_datasource(self, datasource: Datasource):
        customized_datasource = CustomizedDatasource(datasource)
        for collection in datasource.collections:
            customized_collection = CustomizedCollection(collection, customized_datasource)
            self.composite_datasource.add_collection(customized_collection)
            customized_datasource.add_collection(customized_collection)

        for collection in self.composite_datasource.collections:
            # second loop is mandatory to have all collection set
            create_json_api_schema(collection)

    def customize_collection(self, collection_name: str) -> CustomizedCollection:
        collection = self.composite_datasource.get_collection(collection_name)
        return collection
