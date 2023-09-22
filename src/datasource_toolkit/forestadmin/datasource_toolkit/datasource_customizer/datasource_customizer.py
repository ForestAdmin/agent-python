from typing import List, Optional, Union

from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.types import DataSourceOptions
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.types import DataSourceChartDefinition
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
from forestadmin.datasource_toolkit.decorators.publication.datasource import PublicationDataSourceDecorator
from forestadmin.datasource_toolkit.decorators.rename_collection.datasource import RenameCollectionDataSourceDecorator


class DatasourceCustomizer:
    def __init__(self) -> None:
        self.composite_datasource: Datasource = Datasource()
        self.stack = DecoratorStack(self.composite_datasource)

    def add_datasource(self, datasource: Datasource, options: Optional[DataSourceOptions] = None):
        if options is None:
            options = {}

        if "include" in options or "exclude" in options:
            publication_decorator = PublicationDataSourceDecorator(datasource)
            publication_decorator.keep_collections_matching(options.get("include", []), options.get("exclude", []))
            datasource = publication_decorator

        if "rename" in options:
            rename_decorator = RenameCollectionDataSourceDecorator(datasource)
            rename_decorator.rename_collections(options.get("rename", {}))
            datasource = rename_decorator

        for collection in datasource.collections:
            self.composite_datasource.add_collection(collection)

        self.stack = DecoratorStack(self.composite_datasource)

    def customize_collection(self, collection_name: str) -> CollectionCustomizer:
        return CollectionCustomizer(self, self.stack, collection_name)

    def add_chart(self, name: str, definition: DataSourceChartDefinition):
        self.stack.chart.add_chart(name, definition)

    def remove_collections(self, names: Union[str, List[str]]):
        self.stack.publication.keep_collections_matching([], [names] if isinstance(names, str) else names)
