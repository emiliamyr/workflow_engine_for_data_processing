"""Simple in-memory pipeline components for the first development stage."""

from collections.abc import Iterable

from workflow_engine.base import (
    DEFAULT_BATCH_SIZE,
    BaseExtractor,
    BaseLoader,
    BaseTransformer,
    Batch,
    Record,
)


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
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        for index in range(0, len(self.records), batch_size):
            yield self.records[index : index + batch_size]


class SelectColumnsTransformer(BaseTransformer):
    """Keep only selected fields in each record."""

    def __init__(self, columns: Iterable[str]) -> None:
        """Initialize a column-selecting transformer.

        Args:
            columns: Field names to keep.
        """
        self.columns = tuple(columns)

    def transform(self, batch: Batch) -> Batch:
        """Keep selected fields in each record.

        Args:
            batch: Records to transform.

        Returns:
            Records containing only the selected fields.
        """
        return [
            {column: record[column] for column in self.columns if column in record}
            for record in batch
        ]


class ListLoader(BaseLoader):
    """Collect all batches in a list kept in memory."""

    def load(self, batches: Iterable[Batch]) -> list[Record]:
        """Collect records from all batches.

        Args:
            batches: Record batches to collect.

        Returns:
            All records as a single list.
        """
        return [record for batch in batches for record in batch]
