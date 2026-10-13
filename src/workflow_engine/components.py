"""Simple in-memory pipeline components for the first development stage."""

from collections.abc import Iterable
from typing import Any

from workflow_engine.base import BaseExtractor, BaseLoader, BaseTransformer, Batch, Record


class InMemoryExtractor(BaseExtractor):
    """Yield records from memory in batches."""

    def __init__(self, records: Iterable[Record]) -> None:
        self.records = list(records)

    def extract(self, batch_size: int = 100) -> Iterable[Batch]:
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        for index in range(0, len(self.records), batch_size):
            yield self.records[index : index + batch_size]


class SelectColumnsTransformer(BaseTransformer):
    """Keep only selected fields in each record."""

    def __init__(self, columns: Iterable[str]) -> None:
        self.columns = tuple(columns)

    def transform(self, batch: Batch) -> Batch:
        return [
            {column: record[column] for column in self.columns if column in record}
            for record in batch
        ]


class ListLoader(BaseLoader):
    """Collect all batches in a list kept in memory."""

    def load(self, batches: Iterable[Batch]) -> list[Record]:
        return [record for batch in batches for record in batch]
