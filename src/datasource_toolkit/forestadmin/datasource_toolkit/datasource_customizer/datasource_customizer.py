from typing import Dict, List, Optional, Union

from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.types import DataSourceOptions
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.types import DataSourceChartDefinition
from forestadmin.datasource_toolkit.decorators.decorator_stack import DecoratorStack
from forestadmin.datasource_toolkit.decorators.publication.datasource import PublicationDataSourceDecorator
from forestadmin.datasource_toolkit.decorators.rename_collection.datasource import RenameCollectionDataSourceDecorator
from typing_extensions import Self


class DatasourceCustomizer:
    def __init__(self) -> None:
        self.composite_datasource: Datasource = Datasource()
        self.stack = DecoratorStack(self.composite_datasource)

    @property
    def schema(self):
        return self.stack.validation.schema

    async def get_datasource(self):
        await self.stack.apply_queue_customization()
        return self.stack.datasource

    @property
    def collections(self):
        return [self.get_collection(c.name) for c in self.stack.validation.collections]

    def add_datasource(self, datasource: Datasource, options: Optional[DataSourceOptions] = None) -> Self:
        if options is None:
            options = {}

        async def _add_datasource():
            nonlocal datasource
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

        self.stack.queue_customization(_add_datasource)
        return self

    def customize_collection(self, collection_name: str) -> CollectionCustomizer:
        return self.get_collection(collection_name)

    def get_collection(self, collection_name: str) -> CollectionCustomizer:
        return CollectionCustomizer(self, self.stack, collection_name)

    def add_chart(self, name: str, definition: DataSourceChartDefinition) -> Self:
        async def _add_chart():
            self.stack.chart.add_chart(name, definition)

        self.stack.queue_customization(_add_chart)
        return self

    def remove_collections(self, names: Union[str, List[str]]) -> Self:
        async def _remove_collections():
            self.stack.publication.keep_collections_matching([], [names] if isinstance(names, str) else names)

        self.stack.queue_customization(_remove_collections)
        return self

    def use(self, plugin: type, options: Optional[Dict] = {}) -> Self:
        async def _use():
            plugin().run(self, None, options)

        self.stack.queue_customization(_use)
        return self
