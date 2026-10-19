"""Abstract interfaces for pipeline components.

This module defines foundational protocols and base classes for data extractors,
transformers, and loaders within the workflow engine.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

Record = dict[str, Any]
Batch = list[Record]


class BaseExtractor(ABC):
    """Abstract base class for reading records from a data source."""

    @abstractmethod
    def extract(self, batch_size: int = 100) -> Iterable[Batch]:
        """Yield records in batches from the underlying source.

        Args:
            batch_size: Maximum records per batch. Defaults to 100.

        Yields:
            Iterable[Batch]: An iterable stream delivering batches of records.
        """
        raise NotImplementedError


class BaseTransformer(ABC):
    """Abstract base class for transforming batches of data."""

    @abstractmethod
    def transform(self, batch: Batch) -> Batch:
        """Transform a single batch of input records.

        Args:
            batch: List of record dicts representing the input batch.

        Returns:
            Batch: The processed list of record dictionaries.
        """
        raise NotImplementedError


class BaseLoader(ABC):
    """Abstract base class for writing record batches to a target destination."""

    @abstractmethod
    def load(self, batches: Iterable[Batch]) -> Any:
        """Write multiple batches of records to the target destination.

        Args:
            batches: An iterable stream of record batches to be loaded.

        Returns:
            Any: Optional operational metadata or result summary from loading.
        """
        raise NotImplementedError
