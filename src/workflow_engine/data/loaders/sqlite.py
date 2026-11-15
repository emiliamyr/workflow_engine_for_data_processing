"""SQLite data loaders."""

import sqlite3
from collections.abc import Iterable

from workflow_engine.base import BaseLoader, Batch


class SqliteLoader(BaseLoader):
    """Create a SQLite table and insert record batches incrementally."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> None:
        """Initialize a SQLite loader.

        Args:
            connection: SQLite connection used for inserts.
            table_name: Destination table name.
        """
        if not table_name.isidentifier():
            raise ValueError("table_name must be a valid identifier")
        self.connection = connection
        self.table_name = table_name

    def load(self, batches: Iterable[Batch]) -> int:
        """Insert records into the destination table batch by batch.

        The table is created from the first record when it does not exist.
        Values are stored using SQLite's dynamic typing. Each batch is
        committed before the next batch is processed.

        Args:
            batches: Record batches to insert.

        Returns:
            Number of inserted records.
        """
        columns: list[str] | None = None
        inserted_count = 0

        for batch in batches:
            if not batch:
                continue
            if columns is None:
                columns = list(batch[0])
                if not all(column.isidentifier() for column in columns):
                    raise ValueError("record keys must be valid identifiers")
                self._create_table(columns)

            self._insert_batch(batch, columns)
            inserted_count += len(batch)

        return inserted_count

    def _create_table(self, columns: list[str]) -> None:
        """Create the destination table from the first batch."""
        quoted_table = f'"{self.table_name}"'
        definitions = ", ".join(f'"{column}"' for column in columns)
        self.connection.execute(
            f"CREATE TABLE IF NOT EXISTS {quoted_table} ({definitions})",
        )

    def _insert_batch(self, batch: Batch, columns: list[str]) -> None:
        """Insert one batch and commit it immediately."""
        quoted_table = f'"{self.table_name}"'
        quoted_columns = ", ".join(f'"{column}"' for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        self.connection.executemany(
            f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders})",
            [[record.get(column) for column in columns] for record in batch],
        )
        self.connection.commit()
