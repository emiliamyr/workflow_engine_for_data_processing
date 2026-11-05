"""Build and run a dependency-aware pipeline."""

from workflow_engine import Pipeline, task


@task
def extract() -> list[int]:
    return [1, 2, 3]


@task(depends_on=("extract",))
def total(values: list[int]) -> int:
    return sum(values)


pipeline = Pipeline()
pipeline.add(total)
pipeline.add(extract)

print(pipeline.run())
