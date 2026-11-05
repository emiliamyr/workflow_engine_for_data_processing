import pytest

from workflow_engine import Pipeline, task


def test_pipeline_runs_jobs_in_dependency_order() -> None:
    pipeline = Pipeline()

    @task
    def extract() -> list[int]:
        return [1, 2, 3]

    @task(depends_on=("extract",))
    def total(values: list[int]) -> int:
        return sum(values)

    pipeline.add(total)
    pipeline.add(extract)

    assert pipeline.run() == {
        "extract": [1, 2, 3],
        "total": 6,
    }


def test_pipeline_passes_multiple_dependency_results_in_declaration_order() -> None:
    pipeline = Pipeline()

    @task
    def left() -> int:
        return 2

    @task
    def right() -> int:
        return 3

    @task(depends_on=("left", "right"))
    def combine(first: int, second: int) -> int:
        return first + second

    pipeline.add(combine)
    pipeline.add(right)
    pipeline.add(left)

    assert pipeline.run()["combine"] == 5


def test_pipeline_rejects_unknown_dependency() -> None:
    pipeline = Pipeline()

    @task(depends_on=("missing",))
    def process(value: int) -> int:
        return value

    pipeline.add(process)

    with pytest.raises(ValueError, match="unknown job"):
        pipeline.run()


def test_pipeline_rejects_cycles() -> None:
    pipeline = Pipeline()

    @task(name="first", depends_on=("second",))
    def first(value: int) -> int:
        return value

    @task(name="second", depends_on=("first",))
    def second(value: int) -> int:
        return value

    pipeline.add(first)
    pipeline.add(second)

    with pytest.raises(ValueError, match="acyclic"):
        pipeline.run()


def test_pipeline_rejects_duplicate_job_names() -> None:
    pipeline = Pipeline()

    @task
    def load() -> None:
        return None

    @task(name="load")
    def other() -> None:
        return None

    pipeline.add(load)

    with pytest.raises(ValueError, match="already added"):
        pipeline.add(other)
