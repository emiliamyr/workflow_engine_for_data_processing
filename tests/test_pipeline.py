import pytest

from workflow_engine import Pipeline, job


def test_pipeline_runs_jobs_in_dependency_order() -> None:
    pipeline = Pipeline()

    @job
    def extract() -> list[int]:
        return [1, 2, 3]

    @job(depends_on=("extract",))
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

    @job
    def left() -> int:
        return 2

    @job
    def right() -> int:
        return 3

    @job(depends_on=("left", "right"))
    def combine(first: int, second: int) -> int:
        return first + second

    pipeline.add(combine)
    pipeline.add(right)
    pipeline.add(left)

    assert pipeline.run()["combine"] == 5


def test_pipeline_rejects_unknown_dependency() -> None:
    pipeline = Pipeline()

    @job(depends_on=("missing",))
    def process(value: int) -> int:
        return value

    pipeline.add(process)

    with pytest.raises(ValueError, match="unknown job"):
        pipeline.run()


def test_pipeline_rejects_cycles() -> None:
    pipeline = Pipeline()

    @job(name="first", depends_on=("second",))
    def first(value: int) -> int:
        return value

    @job(name="second", depends_on=("first",))
    def second(value: int) -> int:
        return value

    pipeline.add(first)
    pipeline.add(second)

    with pytest.raises(ValueError, match="acyclic"):
        pipeline.run()


def test_pipeline_rejects_duplicate_job_names() -> None:
    pipeline = Pipeline()

    @job
    def load() -> None:
        return None

    @job(name="load")
    def other() -> None:
        return None

    pipeline.add(load)

    with pytest.raises(ValueError, match="already added"):
        pipeline.add(other)
