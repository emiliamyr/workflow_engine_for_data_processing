"""Internal utilities for workflow components."""

DEFAULT_ENCODING = "utf-8"


def validate_batch_size(batch_size: int) -> None:
    """Validate the maximum number of records in a batch.

    Args:
        batch_size: Maximum number of records in each batch.

    Raises:
        ValueError: If ``batch_size`` is less than one.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be greater than zero")
