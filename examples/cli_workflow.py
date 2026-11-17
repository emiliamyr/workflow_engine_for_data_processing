"""Example workflow module for the command-line interface."""

from workflow_engine import (
    CleanRecordsTransformer,
    InMemoryExtractor,
    ListLoader,
    Pipeline,
    SelectColumnsTransformer,
    task,
)
from workflow_engine.base import Batch, Record


@task
def extract() -> list[Batch]:
    """Extract sample records in batches."""
    return list(
        InMemoryExtractor(
            [
                {"name": " Ada ", "role": " engineer "},
                {"name": "Grace", "role": " scientist "},
            ],
        ).extract(batch_size=1),
    )


@task(depends_on=("extract",))
def clean(batches: list[Batch]) -> list[Batch]:
    """Clean extracted records."""
    transformer = CleanRecordsTransformer()
    return [transformer.transform(batch) for batch in batches]


@task(depends_on=("clean",))
def select(batches: list[Batch]) -> list[Batch]:
    """Select fields to include in the output."""
    transformer = SelectColumnsTransformer(["name"])
    return [transformer.transform(batch) for batch in batches]


@task(depends_on=("select",))
def load(batches: list[Batch]) -> list[Record]:
    """Collect all records into the final result."""
    return ListLoader().load(batches)


def build_pipeline() -> Pipeline:
    """Build the example extract-transform-load workflow."""
    pipeline = Pipeline()
    pipeline.add(load)
    pipeline.add(select)
    pipeline.add(clean)
    pipeline.add(extract)
    return pipeline
