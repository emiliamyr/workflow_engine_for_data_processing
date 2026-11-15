"""Read a SQLite table and write cleaned records to JSON."""

import sqlite3
from pathlib import Path

from workflow_engine import (
    CleanRecordsTransformer,
    JsonLoader,
    SqlExtractor,
    SqliteLoader,
)


def main() -> None:
    """Create a sample database, read its table, and export the records."""
    output_directory = Path(".artifacts") / "examples"
    output_directory.mkdir(exist_ok=True)
    database_path = output_directory / "example.db"
    json_path = output_directory / "records.json"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """,
        )
        if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO users (name, role) VALUES (?, ?)",
                [
                    (" Ada ", "engineer"),
                    (" Grace ", "scientist"),
                    (" Alan ", "mathematician"),
                ],
            )
            connection.commit()

        extractor = SqlExtractor(
            connection,
            "SELECT id, name, role FROM users ORDER BY id",
        )
        cleaner = CleanRecordsTransformer()
        cleaned_batches = (
            cleaner.transform(batch) for batch in extractor.extract(batch_size=2)
        )
        connection.execute("DROP TABLE IF EXISTS cleaned_users")
        SqliteLoader(connection, "cleaned_users").load(cleaned_batches)

        output_batches = SqlExtractor(
            connection,
            "SELECT id, name, role FROM cleaned_users ORDER BY id",
        ).extract(batch_size=2)
        output_path = JsonLoader(json_path).load(output_batches)

    print(f"Read users from {database_path}")
    print(f"Wrote cleaned records to {output_path}")


if __name__ == "__main__":
    main()
