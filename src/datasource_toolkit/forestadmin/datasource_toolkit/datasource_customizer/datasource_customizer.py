from typing import Dict, Optional

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
        """Retrieve schema of the agent"""
        return self.stack.validation.schema

    async def get_datasource(self):
        await self.stack.apply_queue_customization()
        return self.stack.datasource

    @property
    def collections(self):
        """Get list of customizable collections"""
        return [self.get_collection(c.name) for c in self.stack.validation.collections]

    def add_datasource(self, datasource: Datasource, options: Optional[DataSourceOptions] = None) -> Self:
        """Add a datasource

        Args:
            datasource (Datasource): the datasource to add
            options (DataSourceOptions, optional): the options
        """
        _options: DataSourceOptions = DataSourceOptions() if options is None else options

        async def _add_datasource():
            nonlocal datasource
            if "include" in _options or "exclude" in _options:
                publication_decorator = PublicationDataSourceDecorator(datasource)
                publication_decorator.keep_collections_matching(
                    _options.get("include", []), _options.get("exclude", [])
                )
                datasource = publication_decorator

            if "rename" in _options:
                rename_decorator = RenameCollectionDataSourceDecorator(datasource)
                rename_decorator.rename_collections(_options.get("rename", {}))
                datasource = rename_decorator

            for collection in datasource.collections:
                self.composite_datasource.add_collection(collection)

        self.stack.queue_customization(_add_datasource)
        return self

    def customize_collection(self, collection_name: str) -> CollectionCustomizer:
        """Allow to interact with a decorated collection

        Args:
            collection_name (str): the name of the collection to manipulate

        Returns:
            CollectionCustomizer: collection builder on the given collection name

        Example:
            .customize_collection('books').rename_field('xx', 'yy')
        """
        return self.get_collection(collection_name)

    def get_collection(self, collection_name: str) -> CollectionCustomizer:
        """Get given collection by name

        Args:
            collection_name (str): name of the collection

        Returns:
            CollectionCustomizer: The corresponding collection
        """
        return CollectionCustomizer(self, self.stack, collection_name)

    def add_chart(self, name: str, definition: DataSourceChartDefinition) -> Self:
        """Create a new API chart

        Args:
            name (str): name of the chart
            definition (DataSourceChartDefinition): definition of the chart

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/charts

        Example:
            .add_chart('numCustomers', lambda context, builder: builder.value(123))
        """

        async def _add_chart():
            self.stack.chart.add_chart(name, definition)

        self.stack.queue_customization(_add_chart)
        return self

    def remove_collections(self, *names: str) -> Self:
        """Remove collections from the exported schema (they will still be usable within the agent).

        Args:
            names (List[str]): the collections to remove

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/agent-customization#removing-collections

        Example:
            .remove_collections('aCollectionToRemove', 'anotherCollectionToRemove')
        """

        async def _remove_collections():
            self.stack.publication.keep_collections_matching(None, [*names])

        self.stack.queue_customization(_remove_collections)
        return self

    def use(self, plugin: type, options: Optional[Dict] = {}) -> Self:
        """Load a plugin across all collections

        Args:
            plugin (type): plugin class
            options (Dict, optional): options which need to be passed to the plugin

        Documentation:
            https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/plugins

        Example:
            .use(advancedExportPlugin, {'format': 'xlsx'})
        """

        async def _use():
            await plugin().run(self, None, options)

        self.stack.queue_customization(_use)
        return self
