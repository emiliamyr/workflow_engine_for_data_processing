"""Simple in-memory pipeline components for the first development stage."""

from collections.abc import Iterable
import pandas as pd

from workflow_engine.base import (
    _MIN_BATCH_SIZE,
    DEFAULT_BATCH_SIZE,
    BaseExtractor,
    BaseLoader,
    BaseTransformer,
    Batch,
)


class InMemoryExtractor(BaseExtractor):
    """Yield rows from an in-memory DataFrame in batches."""

    def __init__(self, data: pd.DataFrame) -> None:
        self.data = data

    def extract(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Iterable[Batch]:
        if batch_size < _MIN_BATCH_SIZE:
            raise ValueError("batch_size must be greater than zero")

        for index in range(0, len(self.data), batch_size):
            yield self.data.iloc[index : index + batch_size].copy()


class SelectColumnsTransformer(BaseTransformer):
    """Keep only selected columns in each batch."""

    def __init__(self, columns: Iterable[str]) -> None:
        self.columns = tuple(columns)

    def transform(self, batch: Batch) -> Batch:
        columns = [column for column in self.columns if column in batch.columns]
        return batch.loc[:, columns].copy()


class ListLoader(BaseLoader):
    """Collect all batches in a DataFrame kept in memory."""

    def load(self, batches: Iterable[Batch]) -> pd.DataFrame:
        frames = list(batches)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
