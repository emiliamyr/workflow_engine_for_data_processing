import asyncio
import threading
from collections.abc import Iterable, Iterator

import pytest

from workflow_engine import Pipeline, task
from workflow_engine.base import Batch


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


def test_pipeline_maps_batch_tasks_lazily() -> None:
    pipeline = Pipeline()
    processed: list[tuple[str, int]] = []

    @task(batch=True)
    def extract() -> Iterator[Batch]:
        for value in (1, 2):
            processed.append(("extract", value))
            yield [{"value": value}]

    @task(batch=True, depends_on=("extract",))
    def increment(batch: Batch) -> Batch:
        value = batch[0]["value"]
        assert isinstance(value, int)
        processed.append(("increment", value))
        return [{"value": value + 1}]

    @task(depends_on=("increment",))
    def collect(batches: Iterable[Batch]) -> list[int]:
        values = []
        for batch in batches:
            value = batch[0]["value"]
            assert isinstance(value, int)
            values.append(value)
        return values

    pipeline.add(collect)
    pipeline.add(increment)
    pipeline.add(extract)

    results = pipeline.run()

    assert results["collect"] == [2, 3]
    assert processed == [
        ("extract", 1),
        ("increment", 1),
        ("extract", 2),
        ("increment", 2),
    ]
    assert set(pipeline.batch_jobs()) == {"extract", "increment"}
    assert pipeline.last_report is not None
    assert all(report.status == "succeeded" for report in pipeline.last_report.tasks)


def test_pipeline_rejects_batch_stream_fan_out() -> None:
    pipeline = Pipeline()

    @task(batch=True)
    def extract() -> Iterator[Batch]:
        yield [{"value": 1}]

    @task(depends_on=("extract",))
    def first_sink(batches: Iterable[Batch]) -> int:
        return sum(len(batch) for batch in batches)

    @task(depends_on=("extract",))
    def second_sink(batches: Iterable[Batch]) -> int:
        return sum(len(batch) for batch in batches)

    pipeline.add(extract)
    pipeline.add(first_sink)
    pipeline.add(second_sink)

    with pytest.raises(ValueError, match="exactly one downstream consumer"):
        pipeline.run()


def test_batch_task_requires_a_batch_dependency() -> None:
    pipeline = Pipeline()

    @task
    def extract() -> list[Batch]:
        return [[{"value": 1}]]

    @task(batch=True, depends_on=("extract",))
    def transform(batch: Batch) -> Batch:
        return batch

    pipeline.add(extract)
    pipeline.add(transform)

    with pytest.raises(ValueError, match="must depend on a batch task"):
        pipeline.run()


def test_pipeline_rejects_unconsumed_batch_stream() -> None:
    pipeline = Pipeline()

    @task(batch=True)
    def extract() -> Iterator[Batch]:
        yield [{"value": 1}]

    @task(depends_on=("extract",))
    def ignore(_batches: Iterable[Batch]) -> str:
        return "ignored"

    pipeline.add(ignore)
    pipeline.add(extract)

    with pytest.raises(RuntimeError, match="not fully consumed"):
        pipeline.run()


@pytest.mark.asyncio
async def test_run_async_supports_synchronous_batch_tasks() -> None:
    pipeline = Pipeline()

    @task(batch=True)
    def extract() -> Iterator[Batch]:
        yield [{"value": 2}]
        yield [{"value": 3}]

    @task(batch=True, depends_on=("extract",))
    def double(batch: Batch) -> Batch:
        value = batch[0]["value"]
        assert isinstance(value, int)
        return [{"value": value * 2}]

    @task(depends_on=("double",))
    async def collect(batches: Iterable[Batch]) -> int:
        total = 0
        for batch in batches:
            value = batch[0]["value"]
            assert isinstance(value, int)
            total += value
        return total

    pipeline.add(collect)
    pipeline.add(double)
    pipeline.add(extract)

    results = await pipeline.run_async()

    assert results["collect"] == 10
    assert pipeline.last_report is not None
    assert all(report.status == "succeeded" for report in pipeline.last_report.tasks)


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


def test_pipeline_exposes_dependency_graph() -> None:
    pipeline = Pipeline()

    @task
    def extract() -> list[int]:
        return [1, 2, 3]

    @task(depends_on=("extract",))
    def total(values: list[int]) -> int:
        return sum(values)

    pipeline.add(total)
    pipeline.add(extract)

    assert pipeline.dependency_graph() == {
        "extract": (),
        "total": ("extract",),
    }


def test_pipeline_run_records_task_and_pipeline_metrics() -> None:
    pipeline = Pipeline()

    @task
    def extract() -> int:
        return 42

    pipeline.add(extract)

    assert pipeline.run() == {"extract": 42}
    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "succeeded"
    assert pipeline.last_report.duration_seconds >= 0
    assert pipeline.last_report.tasks[0].name == "extract"
    assert pipeline.last_report.tasks[0].status == "succeeded"
    assert pipeline.last_report.tasks[0].duration_seconds is not None


def test_pipeline_records_failure_and_skips_remaining_sync_tasks() -> None:
    pipeline = Pipeline()

    @task
    def fail() -> None:
        raise ValueError("task failed")

    @task
    def not_run() -> None:
        pytest.fail("subsequent task must not run")

    pipeline.add(fail)
    pipeline.add(not_run)

    with pytest.raises(ValueError, match="task failed"):
        pipeline.run()

    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "failed"
    assert {task.name: task.status for task in pipeline.last_report.tasks} == {
        "fail": "failed",
        "not_run": "skipped",
    }


@pytest.mark.asyncio
async def test_run_async_parallelizes_independent_tasks_and_awaits_dependencies() -> (
    None
):
    pipeline = Pipeline()
    both_started = asyncio.Event()
    started: set[str] = set()

    async def start(name: str, result: int) -> int:
        started.add(name)
        if len(started) == 2:
            both_started.set()
        await asyncio.wait_for(both_started.wait(), timeout=2)
        return result

    @task
    async def left() -> int:
        return await start("left", 2)

    @task
    async def right() -> int:
        return await start("right", 3)

    @task(depends_on=("left", "right"))
    async def combine(first: int, second: int) -> int:
        assert started == {"left", "right"}
        return first + second

    pipeline.add(combine)
    pipeline.add(left)
    pipeline.add(right)

    assert await pipeline.run_async() == {
        "left": 2,
        "right": 3,
        "combine": 5,
    }
    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "succeeded"
    assert all(task.status == "succeeded" for task in pipeline.last_report.tasks)


@pytest.mark.asyncio
async def test_run_async_runs_sync_jobs_inline() -> None:
    pipeline = Pipeline()
    event_loop_thread = threading.get_ident()

    @task
    def sync_job() -> int:
        return threading.get_ident()

    @task
    async def async_job() -> int:
        return threading.get_ident()

    pipeline.add(sync_job)
    pipeline.add(async_job)

    results = await pipeline.run_async()

    assert results == {
        "sync_job": event_loop_thread,
        "async_job": event_loop_thread,
    }


def test_sync_run_rejects_async_tasks() -> None:
    pipeline = Pipeline()

    @task
    async def async_job() -> int:
        return 42

    pipeline.add(async_job)

    with pytest.raises(TypeError, match="use run_async"):
        pipeline.run()

    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "failed"
    assert pipeline.last_report.tasks[0].status == "failed"


@pytest.mark.asyncio
async def test_run_async_records_failed_and_skipped_tasks() -> None:
    pipeline = Pipeline()

    @task
    async def fail() -> None:
        raise ValueError("task failed")

    @task(depends_on=("fail",))
    async def dependent() -> None:
        pytest.fail("dependent task must be skipped")

    pipeline.add(dependent)
    pipeline.add(fail)

    with pytest.raises(ValueError, match="task failed"):
        await pipeline.run_async()

    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "failed"
    assert {task.name: task.status for task in pipeline.last_report.tasks} == {
        "fail": "failed",
        "dependent": "skipped",
    }


@pytest.mark.asyncio
async def test_run_async_records_cancelled_tasks() -> None:
    pipeline = Pipeline()

    @task
    async def wait_forever() -> None:
        await asyncio.Event().wait()

    @task(depends_on=("wait_forever",))
    async def dependent() -> None:
        return None

    pipeline.add(wait_forever)
    pipeline.add(dependent)
    execution = asyncio.create_task(pipeline.run_async())
    await asyncio.sleep(0.01)
    execution.cancel()

    with pytest.raises(asyncio.CancelledError):
        await execution

    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "failed"
    assert all(task.status == "skipped" for task in pipeline.last_report.tasks)


@pytest.mark.asyncio
async def test_run_async_does_not_treat_cancelled_task_as_success() -> None:
    pipeline = Pipeline()

    @task
    async def cancel() -> None:
        raise asyncio.CancelledError

    pipeline.add(cancel)

    with pytest.raises(asyncio.CancelledError):
        await pipeline.run_async()

    assert pipeline.last_report is not None
    assert pipeline.last_report.status == "failed"
    assert pipeline.last_report.tasks[0].status == "skipped"
