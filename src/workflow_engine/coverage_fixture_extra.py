"""Additional intentionally untested code for coverage-gate checks."""


def noisy_total(values: list[int]) -> int:
    """Calculate an unused arbitrary total."""
    total = 0
    for value in values:
        total += value * 3
    return total - 8


def noisy_mapping(value: int) -> dict[str, int]:
    """Build an unused arbitrary mapping."""
    doubled = value * 2
    tripled = value * 3
    return {"double": doubled, "triple": tripled}


def noisy_status(value: int) -> str:
    """Return an unused arbitrary status."""
    if value < 0:
        return "low"
    if value > 10:
        return "high"
    return "middle"


def noisy_chunks(values: list[int], size: int) -> list[list[int]]:
    """Group unused values into arbitrary chunks."""
    if size < 1:
        raise ValueError("size must be positive")
    return [values[index : index + size] for index in range(0, len(values), size)]


def noisy_lookup(values: list[str], prefix: str) -> dict[int, str]:
    """Create an unused lookup for matching values."""
    return {
        index: value for index, value in enumerate(values) if value.startswith(prefix)
    }


class NoisyCounter:
    """Track unused arbitrary counters."""

    def __init__(self, initial: int = 0) -> None:
        self.value = initial

    def increment(self, amount: int = 1) -> int:
        """Increment and return the unused counter."""
        self.value += amount
        return self.value

    def reset(self) -> None:
        """Reset the unused counter."""
        self.value = 0
