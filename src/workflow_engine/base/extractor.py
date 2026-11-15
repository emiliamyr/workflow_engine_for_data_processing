"""Base interface for extracting records."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from workflow_engine.base.types import DEFAULT_BATCH_SIZE, Batch


class BaseExtractor(ABC):
    """Read records from a data source."""

    @abstractmethod
    def extract(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[Batch]:
        """Yield records in batches.

        Args:
            batch_size: Maximum number of records in each batch.

        Returns:
            An iterable of record batches.
        """
        raise NotImplementedError
