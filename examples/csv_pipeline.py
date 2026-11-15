"""Read a CSV file and write cleaned records to JSON."""

from pathlib import Path

from workflow_engine import CleanRecordsTransformer, CsvExtractor, JsonLoader


def main() -> None:
    """Create a sample CSV file, process it, and export JSON output."""
    output_directory = Path(".artifacts") / "examples"
    output_directory.mkdir(exist_ok=True)
    csv_path = output_directory / "example.csv"
    json_path = output_directory / "csv_records.json"
    csv_path.write_text(
        "name,role,active\nAda, engineer ,true\nGrace, scientist ,true\n",
        encoding="utf-8",
    )

    extractor = CsvExtractor(csv_path)
    cleaner = CleanRecordsTransformer()
    cleaned_batches = (
        cleaner.transform(batch) for batch in extractor.extract(batch_size=1)
    )
    output_path = JsonLoader(json_path).load(cleaned_batches)

    print(f"Read records from {csv_path}")
    print(f"Wrote cleaned records to {output_path}")


if __name__ == "__main__":
    main()
