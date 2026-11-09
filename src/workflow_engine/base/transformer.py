"""Base interface for transforming records."""

from abc import ABC, abstractmethod

from workflow_engine.base.types import Batch


class BaseTransformer(ABC):
    """Transform one batch of records."""

    @abstractmethod
    def transform(self, batch: Batch) -> Batch:
        """Return the transformed batch."""
        raise NotImplementedError
