"""Shared types for pipeline components.

``Record`` is a mutable mapping of string keys to values. ``Batch`` groups
records passed between pipeline stages.
"""

from collections.abc import MutableMapping

DEFAULT_BATCH_SIZE = 100

Record = MutableMapping[str, object]
Batch = list[Record]
