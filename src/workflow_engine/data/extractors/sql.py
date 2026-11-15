"""SQL data extractors."""

import sqlite3
from collections.abc import Iterable, Sequence

from workflow_engine.base import DEFAULT_BATCH_SIZE, BaseExtractor, Batch


class SqlExtractor(BaseExtractor):
    """Read rows from a SQLite query in batches."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        query: str,
        parameters: Sequence[object] = (),
    ) -> None:
        """Initialize a SQL extractor.

        Args:
            connection: SQLite connection used to execute the query.
            query: SQL query returning the records to extract.
            parameters: Positional values bound to the query.
        """
        self.connection = connection
        self.query = query
        self.parameters = tuple(parameters)

    def extract(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[Batch]:
        """Yield query rows in batches.

        Args:
            batch_size: Maximum number of rows in each batch.

        Returns:
            An iterable of query rows grouped into batches.

        Raises:
            ValueError: If ``batch_size`` is less than one.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        cursor = self.connection.execute(self.query, self.parameters)
        try:
            columns = [column[0] for column in cursor.description or ()]
            while rows := cursor.fetchmany(batch_size):
                yield [dict(zip(columns, row, strict=True)) for row in rows]
        finally:
            cursor.close()
