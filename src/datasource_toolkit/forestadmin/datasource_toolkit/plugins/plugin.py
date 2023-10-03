from abc import ABC, abstractmethod
from typing import Dict, Optional


class Plugin(ABC):
    @abstractmethod
    async def run(
        self,
        datasource_customizer: "DatasourceCustomizer",  # noqa: F821
        collection_customizer: Optional["CollectionCustomizer"] = None,  # noqa: F821
        options: Optional[Dict] = {},
    ) -> None:
        """plugin function to implement"""
