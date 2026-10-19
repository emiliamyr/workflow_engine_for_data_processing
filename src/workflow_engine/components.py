"""Simple in-memory pipeline components for the first development stage."""

from collections.abc import Iterable

from workflow_engine._base import (
    BaseExtractor,
    BaseLoader,
    BaseTransformer,
    Batch,
    Record,
)


class InMemoryExtractor(BaseExtractor):
    """Yield records from memory in batches."""

    def __init__(self, records: Iterable[Record]) -> None:
        """Initialize the extractor with an in-memory collection of records.

        Args:
            records: An iterable of record dictionaries to be extracted.
        """
        self.records = list(records)

    def extract(self, batch_size: int = 100) -> Iterable[Batch]:
        """Yield records from memory in chunks of a specified size.

        Args:
            batch_size: The maximum number of records to include in each batch.
                Must be greater than zero. Defaults to 100.

        Yields:
            Iterable[Batch]: A generator yielding consecutive batches of records.

        Raises:
            ValueError: If `batch_size` is less than 1.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        for index in range(0, len(self.records), batch_size):
            yield self.records[index : index + batch_size]


class SelectColumnsTransformer(BaseTransformer):
    """Keep only selected fields in each record."""

    def __init__(self, columns: Iterable[str]) -> None:
        """Initialize the transformer with the set of allowed column names.

        Args:
            columns: An iterable of field names to retain in each record.
        """
        self.columns = tuple(columns)

    def transform(self, batch: Batch) -> Batch:
        """Filter fields in each record, preserving only specified columns.

        Args:
            batch: A list of record dictionaries to transform.

        Returns:
            Batch: New batch with records containing only chosen columns.
        """
        return [
            {column: record[column] for column in self.columns if column in record}
            for record in batch
        ]


class ListLoader(BaseLoader):
    """Collect all batches in a list kept in memory."""

    def load(self, batches: Iterable[Batch]) -> list[Record]:
        """Flatten and merge all incoming record batches into a single in-memory list.

        Args:
            batches: An iterable stream of record batches to consume.

        Returns:
            list[Record]: A single flattened list containing all loaded records.
        """
        return [record for batch in batches for record in batch]
