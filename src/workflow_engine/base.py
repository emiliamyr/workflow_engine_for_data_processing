"""Abstract interfaces for pipeline components."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, MutableMapping

DEFAULT_BATCH_SIZE = 100
_MIN_BATCH_SIZE = 1

Record = MutableMapping[str, object]
Batch = list[Record]


class BaseExtractor(ABC):
    """Read records from a data source."""

    @abstractmethod
    def extract(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[Batch]:
        """Yield records in batches."""
        raise NotImplementedError


class BaseTransformer(ABC):
    """Transform one batch of records."""

    @abstractmethod
    def transform(self, batch: Batch) -> Batch:
        """Return the transformed batch."""
        raise NotImplementedError


class BaseLoader(ABC):
    """Write batches of records to a destination."""

    @abstractmethod
    def load(self, batches: Iterable[Batch]) -> object:
        """Load batches and return an optional result."""
        raise NotImplementedError
