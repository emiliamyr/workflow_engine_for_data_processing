import pytest

from workflow_engine.tasks import TaskSpec, task


def test_task_keeps_function_callable_and_stores_metadata() -> None:
    @task
    def extract() -> list[dict[str, int]]:
        return [{"value": 1}]

    assert extract() == [{"value": 1}]
    assert extract.task_spec == TaskSpec("extract", ())


def test_task_accepts_name_and_dependencies() -> None:
    @task(name="clean_data", depends_on=("extract_data",))
    def clean() -> str:
        return "done"

    assert clean() == "done"
    assert clean.task_spec.name == "clean_data"
    assert clean.task_spec.dependencies == ("extract_data",)


def test_task_marks_batch_mode() -> None:
    @task(name="clean_batch", depends_on=("extract_batches",), batch=True)
    def clean(batch: list[dict[str, int]]) -> list[dict[str, int]]:
        return batch

    assert clean.task_spec.batch is True


def test_batch_task_rejects_multiple_dependencies() -> None:
    with pytest.raises(ValueError, match="at most one dependency"):

        @task(depends_on=("left", "right"), batch=True)
        def combine(left: list[int]) -> list[int]:
            return left


def test_batch_task_rejects_async_functions() -> None:
    with pytest.raises(TypeError, match="must be synchronous"):

        @task(batch=True)
        async def transform(batch: list[int]) -> list[int]:
            return batch
