from typing import Dict

from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack


class DatasourceCustomizer:
    def __init__(self) -> None:
        self.composite_datasource: Datasource = Datasource()
        self.stack = DecoratorStack(self.composite_datasource)

    def add_datasource(self, datasource: Datasource, options: Dict):
        # if "include" in options or "exclude" in options:
        #     $datasource = new PublicationCollectionDatasourceDecorator($datasource);
        #     $datasource->build();
        #     $datasource->keepCollectionsMatching($options['include'] ?? [], $options['exclude'] ?? []);

        # if "rename" in options:
        #     $datasource = new RenameCollectionDatasourceDecorator($datasource);
        #     $datasource->build();
        #     $datasource->renameCollections($options['rename'] ?? []);

        for collection in datasource.collections:
            self.composite_datasource.add_collection(collection)

        self.stack = DecoratorStack(self.composite_datasource)

    def customize_collection(self, collection_name: str) -> CollectionCustomizer:
        return CollectionCustomizer(self, self.stack, collection_name)
