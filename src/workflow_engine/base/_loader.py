"""Base interface for loading records."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from workflow_engine.base._types import Batch


class BaseLoader(ABC):
    """Write batches of records to a destination."""

    @abstractmethod
    def load(self, batches: Iterable[Batch]) -> object:
        """Load batches and return the loader-specific result.

        Args:
            batches: Record batches to load.

        Returns:
            The result produced by this loader.
        """
        raise NotImplementedError
