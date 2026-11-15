"""Shared types for pipeline components."""

from collections.abc import MutableMapping

DEFAULT_BATCH_SIZE = 100

Record = MutableMapping[str, object]
Batch = list[Record]
