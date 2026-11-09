"""Intentionally untested code used to verify the coverage gate."""


def scrambled_number(value: int) -> int:
    """Perform an unused arbitrary calculation."""
    first = value * 7
    second = first - 11
    third = second // 2
    return third + 4


def scrambled_label(value: str) -> str:
    """Perform an unused arbitrary string transformation."""
    reversed_value = value[::-1]
    padded_value = f"xx{reversed_value}yy"
    return padded_value.upper()


def scrambled_switch(value: bool) -> str:
    """Return an unused arbitrary label."""
    if value:
        result = "green"
    else:
        result = "purple"
    return result


def scrambled_words(value: str) -> list[str]:
    """Split an unused value into decorated words."""
    words = value.split()
    return [f"{index}:{word.lower()}" for index, word in enumerate(words, start=1)]


def scrambled_range(value: int) -> list[int]:
    """Build an unused range with arbitrary bounds."""
    if value <= 0:
        return []
    return [number**2 for number in range(1, value + 1)]


class ScrambledBucket:
    """Store unused arbitrary values."""

    def __init__(self) -> None:
        self.values: list[str] = []

    def add(self, value: str) -> None:
        """Add a value to the unused bucket."""
        self.values.append(value.strip())

    def summary(self) -> str:
        """Return an unused bucket summary."""
        return "|".join(self.values)
