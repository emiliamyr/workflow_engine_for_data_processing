"""In-memory data loaders."""

from collections.abc import Iterable

from workflow_engine.base import BaseLoader, Batch, Record


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
