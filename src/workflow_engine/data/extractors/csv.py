"""CSV data extractors."""

import csv
from collections.abc import Iterable
from pathlib import Path

from workflow_engine.base import DEFAULT_BATCH_SIZE, BaseExtractor, Batch


class CsvExtractor(BaseExtractor):
    """Read dictionary records from a CSV file in batches."""

    def __init__(
        self,
        path: str | Path,
        *,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize a CSV extractor.

        Args:
            path: CSV file to read.
            encoding: Text encoding used to open the file.
        """
        self.path = Path(path)
        self.encoding = encoding

    def extract(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[Batch]:
        """Yield CSV rows in batches.

        Args:
            batch_size: Maximum number of rows in each batch.

        Returns:
            An iterable of CSV rows grouped into batches.

        Raises:
            ValueError: If ``batch_size`` is less than one.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be greater than zero")

        with self.path.open(newline="", encoding=self.encoding) as file:
            reader = csv.DictReader(file)
            batch: Batch = []
            for row in reader:
                batch.append(dict(row))
                if len(batch) == batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch
