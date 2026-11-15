"""Base interface for loading records."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from workflow_engine.base.types import Batch


class BaseLoader(ABC):
    """Write batches of records to a destination."""

    @abstractmethod
    def load(self, batches: Iterable[Batch]) -> object:
        """Load batches and return an optional result."""
        raise NotImplementedError
