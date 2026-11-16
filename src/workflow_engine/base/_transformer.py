"""Base interface for transforming records."""

from abc import ABC, abstractmethod

from workflow_engine.base._types import Batch


class BaseTransformer(ABC):
    """Transform one batch of records."""

    @abstractmethod
    def transform(self, batch: Batch) -> Batch:
        """Transform and return a batch of records.

        Args:
            batch: Records to transform.

        Returns:
            The transformed records.
        """
        raise NotImplementedError
