"""In-memory data extractors."""

from collections.abc import Iterable

from workflow_engine._utils import validate_batch_size
from workflow_engine.base import DEFAULT_BATCH_SIZE, BaseExtractor, Batch, Record


class InMemoryExtractor(BaseExtractor):
    """Yield records from memory in batches."""

    def __init__(self, records: Iterable[Record]) -> None:
        """Initialize an in-memory extractor.

        Args:
            records: Records available for extraction.
        """
        self.records = list(records)

    def extract(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[Batch]:
        """Yield stored records in batches.

        Args:
            batch_size: Maximum number of records in each batch.

        Returns:
            An iterable of record batches.
        """
        validate_batch_size(batch_size)

        for index in range(0, len(self.records), batch_size):
            yield self.records[index : index + batch_size]
