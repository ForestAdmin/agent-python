from abc import ABC, abstractmethod
from typing import Dict, Optional

from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer


class Plugin(ABC):
    @abstractmethod
    async def run(
        datasource_customizer: DatasourceCustomizer,
        collection_customizer: Optional[CollectionCustomizer] = None,
        options: Optional[Dict] = {},
    ) -> None:
        """plugin function to implement"""
