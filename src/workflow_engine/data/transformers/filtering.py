"""Data-filtering transformers."""

from collections.abc import Callable

from workflow_engine.base import BaseTransformer, Batch, Record

RecordPredicate = Callable[[Record], bool]


class FilterRecordsTransformer(BaseTransformer):
    """Keep records matching a supplied predicate."""

    def __init__(self, predicate: RecordPredicate) -> None:
        """Initialize a record-filtering transformer.

        Args:
            predicate: Function returning whether a record should be kept.
        """
        self.predicate = predicate

    def transform(self, batch: Batch) -> Batch:
        """Filter records using the configured predicate.

        Args:
            batch: Records to filter.

        Returns:
            Records for which the predicate returned ``True``.
        """
        return [record for record in batch if self.predicate(record)]
