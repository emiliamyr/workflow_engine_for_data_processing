import json
import sqlite3
from pathlib import Path

import pytest

from workflow_engine import (
    CleanRecordsTransformer,
    CsvExtractor,
    FilterRecordsTransformer,
    JsonLoader,
    SqlExtractor,
    SqliteLoader,
)


def test_csv_extractor_reads_rows_in_batches(tmp_path: Path) -> None:
    path = tmp_path / "records.csv"
    path.write_text("name,active\nAda,true\nGrace,false\n", encoding="utf-8")

    assert list(CsvExtractor(path).extract(batch_size=1)) == [
        [{"name": "Ada", "active": "true"}],
        [{"name": "Grace", "active": "false"}],
    ]


def test_sql_extractor_reads_parameterized_rows() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE TABLE records (name TEXT, active INTEGER)")
        connection.executemany(
            "INSERT INTO records VALUES (?, ?)",
            [("Ada", 1), ("Grace", 0)],
        )

        extractor = SqlExtractor(
            connection,
            "SELECT name, active FROM records WHERE active = ?",
            [1],
        )

        assert list(extractor.extract()) == [[{"name": "Ada", "active": 1}]]
    finally:
        connection.close()


def test_extractors_reject_invalid_batch_size() -> None:
    connection = sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="greater than zero"):
        list(CsvExtractor("records.csv").extract(batch_size=0))
    try:
        with pytest.raises(ValueError, match="greater than zero"):
            list(SqlExtractor(connection, "SELECT 1").extract(batch_size=0))
    finally:
        connection.close()


def test_clean_records_transformer_strips_and_drops_empty_values() -> None:
    transformer = CleanRecordsTransformer(drop_empty_values=True)

    assert transformer.transform(
        [{"name": " Ada ", "email": " ", "active": True}],
    ) == [{"name": "Ada", "active": True}]


def test_filter_records_transformer_keeps_matching_records() -> None:
    transformer = FilterRecordsTransformer(lambda record: record["active"] is True)

    assert transformer.transform(
        [{"name": "Ada", "active": True}, {"name": "Grace", "active": False}],
    ) == [{"name": "Ada", "active": True}]


def test_json_loader_writes_records(tmp_path: Path) -> None:
    path = tmp_path / "records.json"

    assert JsonLoader(path).load([[{"name": "Ada"}], [{"name": "Grace"}]]) == path
    assert json.loads(path.read_text(encoding="utf-8")) == [
        {"name": "Ada"},
        {"name": "Grace"},
    ]


def test_json_loader_preserves_target_if_serialization_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "records.json"
    original_content = '[{"name": "existing"}]'
    path.write_text(original_content, encoding="utf-8")

    def fail_dump(*args: object, **kwargs: object) -> None:
        raise TypeError("record cannot be serialized")

    monkeypatch.setattr(json, "dump", fail_dump)

    with pytest.raises(TypeError, match="cannot be serialized"):
        JsonLoader(path).load([[{"name": "new"}]])

    assert path.read_text(encoding="utf-8") == original_content
    assert list(tmp_path.iterdir()) == [path]


def test_sqlite_loader_creates_table_and_inserts_records() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        loader = SqliteLoader(connection, "records")

        assert loader.load([[{"name": "Ada"}], [{"name": "Grace"}]]) == 2
        assert connection.execute("SELECT name FROM records").fetchall() == [
            ("Ada",),
            ("Grace",),
        ]
    finally:
        connection.close()


def test_sqlite_loader_rejects_invalid_table_name() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        with pytest.raises(ValueError, match="valid identifier"):
            SqliteLoader(connection, "records; DROP TABLE users")
    finally:
        connection.close()
