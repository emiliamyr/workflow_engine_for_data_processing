"""JSON data loaders."""

import json
from collections.abc import Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile

from workflow_engine.base import BaseLoader, Batch


class JsonLoader(BaseLoader):
    """Write batches of records to a JSON array incrementally."""

    def __init__(
        self,
        path: str | Path,
        *,
        indent: int | None = 2,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize a JSON loader.

        Args:
            path: JSON file to write.
            indent: JSON indentation, or ``None`` for compact output.
            encoding: Text encoding used to write the file.
        """
        self.path = Path(path)
        self.indent = indent
        self.encoding = encoding

    def load(self, batches: Iterable[Batch]) -> Path:
        """Write records to the configured JSON file batch by batch.

        The target file is replaced only after the complete JSON array has
        been written.

        Args:
            batches: Record batches to write.

        Returns:
            The path of the written JSON file.
        """
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                "w",
                encoding=self.encoding,
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                file.write("[")
                first_record = True
                for batch in batches:
                    for record in batch:
                        if not first_record:
                            file.write(",")
                        json.dump(record, file, indent=self.indent)
                        first_record = False
                    file.flush()
                file.write("]")
            temporary_path.replace(self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        return self.path
