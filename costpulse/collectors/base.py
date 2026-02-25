"""Abstract base class for all data collectors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import structlog
from databricks.sdk import WorkspaceClient
from databricks.sdk.config import Config

logger = structlog.get_logger()


class BaseCollector(ABC):
    """Abstract base class for all data collectors."""

    def __init__(self, host: str, token: str):
        """Initialize the collector.

        Args:
            host: Databricks workspace URL
            token: Databricks access token
        """
        self.host = host
        self.token = token
        self._client: Optional[WorkspaceClient] = None

    @property
    def client(self) -> WorkspaceClient:
        """Get or create Databricks workspace client.

        Returns:
            WorkspaceClient instance
        """
        if self._client is None:
            config = Config(host=self.host, token=self.token)
            self._client = WorkspaceClient(config=config)
        return self._client

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from the source.

        Returns:
            List of raw data records
        """
        pass

    @abstractmethod
    async def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform raw data into standardized format.

        Args:
            data: Raw data records

        Returns:
            List of transformed data records
        """
        pass

    async def run(self) -> List[Dict[str, Any]]:
        """Execute the collection pipeline.

        Returns:
            List of transformed data records
        """
        logger.info("Starting collection", collector=self.__class__.__name__)
        try:
            raw_data = await self.collect()
            transformed = await self.transform(raw_data)
            logger.info(
                "Collection complete",
                collector=self.__class__.__name__,
                records=len(transformed),
            )
            return transformed
        except Exception as e:
            logger.error("Collection failed", collector=self.__class__.__name__, error=str(e))
            raise
