"""Data-cleaning transformers."""

from workflow_engine.base import BaseTransformer, Batch, Record


class CleanRecordsTransformer(BaseTransformer):
    """Normalize string values and optionally remove empty values."""

    def __init__(self, *, drop_empty_values: bool = False) -> None:
        """Initialize a record-cleaning transformer.

        Args:
            drop_empty_values: Remove fields whose stripped string value is empty.
        """
        self.drop_empty_values = drop_empty_values

    def transform(self, batch: Batch) -> Batch:
        """Clean string values in each record.

        Args:
            batch: Records to clean.

        Returns:
            Records with whitespace removed from string values.
        """
        cleaned_batch: Batch = []
        for record in batch:
            cleaned_record: Record = {}
            for key, value in record.items():
                cleaned_value = value.strip() if isinstance(value, str) else value
                if self.drop_empty_values and cleaned_value == "":
                    continue
                cleaned_record[key] = cleaned_value
            cleaned_batch.append(cleaned_record)
        return cleaned_batch
