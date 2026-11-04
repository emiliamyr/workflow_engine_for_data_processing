"""Examples of the workflow utility decorators."""

from workflow_engine import retry, track_latency


@track_latency
def transform(value: int) -> int:
    """Apply a small transformation while recording execution time."""
    return value * 2


attempts = 0


@retry(max_attempts=3, exceptions=(ValueError,))
def load(value: int) -> str:
    """Demonstrate retrying a transient operation."""
    global attempts
    attempts += 1
    if attempts < 2:
        raise ValueError("temporary failure")
    return f"loaded {value}"


value = transform(21)
print(load(value))
print(f"latency: {transform.last_latency:.6f}s")
