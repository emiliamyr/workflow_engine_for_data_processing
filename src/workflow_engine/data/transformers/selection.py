"""Transformers for selecting record fields."""

from collections.abc import Iterable

from workflow_engine.base import BaseTransformer, Batch


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
