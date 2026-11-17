"""Dependency-aware execution of decorated workflow jobs."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Literal

import networkx as nx

from workflow_engine.tasks import Task

logger = logging.getLogger(__name__)

TaskStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]
PipelineStatus = Literal["succeeded", "failed"]


@dataclass(frozen=True, slots=True)
class TaskReport:
    """Execution status and timing for one workflow task."""

    name: str
    status: TaskStatus
    duration_seconds: float | None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PipelineReport:
    """Overall status, timing, and task reports for one pipeline run."""

    status: PipelineStatus
    duration_seconds: float
    tasks: tuple[TaskReport, ...]


@dataclass(slots=True)
class _TaskState:
    status: TaskStatus = "pending"
    duration_seconds: float | None = None
    error: str | None = None


class Pipeline:
    """Build and execute a directed acyclic graph of jobs."""

    def __init__(self) -> None:
        """Initialize an empty pipeline."""
        self._jobs: dict[str, Task] = {}
        self.last_report: PipelineReport | None = None

    def add(self, job: Task) -> None:
        """Add a uniquely named job to the pipeline.

        Args:
            job: Task to add.
        """
        name = job.task_spec.name
        if name in self._jobs:
            raise ValueError(f"job already added: {name}")
        self._jobs[name] = job

    def dependency_graph(self) -> dict[str, tuple[str, ...]]:
        """Return each task's direct dependencies after validating the graph.

        Returns:
            A mapping from task names to their prerequisite task names.
        """
        execution_order = self._execution_order()
        return {
            name: self._jobs[name].task_spec.dependencies for name in execution_order
        }

    def batch_jobs(self) -> tuple[str, ...]:
        """Return the names of tasks that produce or transform batch streams."""
        return tuple(name for name, job in self._jobs.items() if job.task_spec.batch)

    def run(self) -> dict[str, object]:
        """Execute jobs sequentially in dependency order.

        Returns:
            Results keyed by job name.
        """
        execution_order = self._execution_order()
        states = {name: _TaskState() for name in execution_order}
        results: dict[str, object] = {}
        started_at = time.perf_counter()
        status: PipelineStatus = "failed"

        try:
            for name in execution_order:
                job = self._jobs[name]
                dependency_results = [
                    results[dependency] for dependency in job.task_spec.dependencies
                ]
                state = states[name]
                if job.task_spec.batch:
                    results[name] = self._batch_task_result(
                        job,
                        dependency_results,
                        state,
                    )
                    continue

                state.status = "running"
                logger.info("Starting task %s", name)
                task_started_at = time.perf_counter()
                try:
                    result = job(*dependency_results)
                    if inspect.isawaitable(result):
                        if inspect.iscoroutine(result):
                            result.close()
                        raise TypeError(
                            f"task '{name}' is asynchronous; use run_async()",
                        )
                    results[name] = result
                except Exception as error:
                    state.status = "failed"
                    state.error = f"{type(error).__name__}: {error}"
                    logger.exception("Task %s failed", name)
                    raise
                else:
                    state.status = "succeeded"
                    logger.info(
                        "Finished task %s in %.3f seconds",
                        name,
                        time.perf_counter() - task_started_at,
                    )
                finally:
                    state.duration_seconds = time.perf_counter() - task_started_at
            self._ensure_batch_streams_consumed(states)
            status = "succeeded"
            return results
        except Exception:
            self._close_batch_streams(results)
            for state in states.values():
                if state.status == "pending":
                    state.status = "skipped"
            raise
        finally:
            self.last_report = self._make_report(
                status,
                time.perf_counter() - started_at,
                states,
            )

    async def run_async(self) -> dict[str, object]:
        """Execute independent jobs concurrently while awaiting dependencies.

        Asynchronous task functions can run concurrently. Synchronous task
        functions run inline on the event loop.

        Returns:
            Results keyed by job name.
        """
        execution_order = self._execution_order()
        states = {name: _TaskState() for name in execution_order}
        results: dict[str, object] = {}
        started_at = time.perf_counter()
        status: PipelineStatus = "failed"
        executions: dict[str, asyncio.Task[object]] = {}

        async def execute(name: str) -> object:
            job = self._jobs[name]
            state = states[name]
            try:
                dependency_results = await asyncio.gather(
                    *(
                        executions[dependency]
                        for dependency in job.task_spec.dependencies
                    ),
                )
            except asyncio.CancelledError:
                state.status = "skipped"
                state.error = "A dependency was cancelled."
                raise
            except Exception as error:
                state.status = "skipped"
                state.error = f"Dependency failed: {type(error).__name__}: {error}"
                logger.warning("Skipping task %s because a dependency failed", name)
                raise

            if job.task_spec.batch:
                result = self._batch_task_result(job, dependency_results, state)
                results[name] = result
                return result

            state.status = "running"
            logger.info("Starting task %s", name)
            task_started_at = time.perf_counter()
            try:
                result = await self._execute_async_job(job, *dependency_results)
            except asyncio.CancelledError:
                state.status = "skipped"
                state.error = "Task execution was cancelled."
                raise
            except Exception as error:
                state.status = "failed"
                state.error = f"{type(error).__name__}: {error}"
                logger.exception("Task %s failed", name)
                raise
            else:
                results[name] = result
                state.status = "succeeded"
                logger.info(
                    "Finished task %s in %.3f seconds",
                    name,
                    time.perf_counter() - task_started_at,
                )
                return result
            finally:
                state.duration_seconds = time.perf_counter() - task_started_at

        try:
            executions = {
                name: asyncio.create_task(execute(name), name=name)
                for name in execution_order
            }
            outcomes = await asyncio.gather(
                *executions.values(),
                return_exceptions=True,
            )
            for name, outcome in zip(execution_order, outcomes, strict=True):
                if states[name].status == "failed":
                    if isinstance(outcome, BaseException):
                        raise outcome
                if isinstance(outcome, asyncio.CancelledError):
                    raise outcome
            self._ensure_batch_streams_consumed(states)
            status = "succeeded"
            return results
        except asyncio.CancelledError:
            self._close_batch_streams(results)
            for state in states.values():
                if state.status in ("pending", "running"):
                    state.status = "skipped"
                    state.error = "Pipeline execution was cancelled."
            raise
        except Exception:
            self._close_batch_streams(results)
            raise
        finally:
            self.last_report = self._make_report(
                status,
                time.perf_counter() - started_at,
                states,
            )

    @staticmethod
    async def _execute_async_job(job: Task, *args: object) -> object:
        """Call a task and await it when it returns an awaitable."""
        result = job(*args)
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    def _make_report(
        status: PipelineStatus,
        duration_seconds: float,
        states: dict[str, _TaskState],
    ) -> PipelineReport:
        return PipelineReport(
            status=status,
            duration_seconds=duration_seconds,
            tasks=tuple(
                TaskReport(
                    name=name,
                    status=state.status,
                    duration_seconds=state.duration_seconds,
                    error=state.error,
                )
                for name, state in states.items()
            ),
        )

    def _batch_task_result(
        self,
        job: Task,
        dependency_results: list[object],
        state: _TaskState,
    ) -> Iterator[object]:
        name = job.task_spec.name
        if dependency_results:
            batches = self._map_batches(job, dependency_results[0])
        else:
            batches = self._source_batches(job)
        return self._track_batch_stream(name, batches, state)

    def _source_batches(self, job: Task) -> Iterator[object]:
        name = job.task_spec.name
        source = self._require_synchronous(job(), name)
        yield from self._iter_batches(source, name)

    def _map_batches(self, job: Task, batches: object) -> Iterator[object]:
        name = job.task_spec.name
        for batch in self._iter_batches(batches, name):
            result = self._require_synchronous(job(batch), name)
            if not isinstance(result, list):
                raise TypeError(f"batch task '{name}' must return a batch")
            yield result

    @staticmethod
    def _iter_batches(batches: object, name: str) -> Iterator[list[object]]:
        if not isinstance(batches, Iterable) or isinstance(batches, (str, bytes)):
            raise TypeError(f"batch task '{name}' requires an iterable of batches")
        for batch in batches:
            if not isinstance(batch, list):
                raise TypeError(
                    f"batch task '{name}' received a value that is not a batch"
                )
            yield batch

    @staticmethod
    def _require_synchronous(result: object, name: str) -> object:
        if inspect.isawaitable(result):
            if inspect.iscoroutine(result):
                result.close()
            raise TypeError(f"batch task '{name}' must return synchronously")
        return result

    @staticmethod
    def _track_batch_stream(
        name: str,
        batches: Iterable[object],
        state: _TaskState,
    ) -> Iterator[object]:
        def track() -> Iterator[object]:
            state.status = "running"
            logger.info("Starting task %s", name)
            completed = False
            active_seconds = 0.0
            iterator = iter(batches)
            try:
                while True:
                    step_started_at = time.perf_counter()
                    try:
                        batch = next(iterator)
                    except StopIteration:
                        active_seconds += time.perf_counter() - step_started_at
                        break
                    active_seconds += time.perf_counter() - step_started_at
                    yield batch

                completed = True
                state.status = "succeeded"
                logger.info("Finished task %s in %.3f seconds", name, active_seconds)
            except Exception as error:
                state.status = "failed"
                state.error = f"{type(error).__name__}: {error}"
                logger.exception("Task %s failed", name)
                raise
            finally:
                state.duration_seconds = active_seconds
                if not completed and state.status == "running":
                    state.status = "failed"
                    state.error = "Batch stream was not fully consumed."

        return track()

    def _ensure_batch_streams_consumed(
        self,
        states: dict[str, _TaskState],
    ) -> None:
        unconsumed = [
            name
            for name, job in self._jobs.items()
            if job.task_spec.batch and states[name].status != "succeeded"
        ]
        if not unconsumed:
            return

        for name in unconsumed:
            state = states[name]
            if state.status in ("pending", "running"):
                state.status = "failed"
                state.error = "Batch stream was not fully consumed."
        names = ", ".join(unconsumed)
        raise RuntimeError(f"batch task streams were not fully consumed: {names}")

    def _close_batch_streams(self, results: dict[str, object]) -> None:
        for name, result in results.items():
            if not self._jobs[name].task_spec.batch:
                continue
            close = getattr(result, "close", None)
            if callable(close):
                close()

    def _execution_order(self) -> list[str]:
        graph = self._build_graph()
        try:
            execution_order = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("pipeline dependencies must be acyclic") from None
        for name in execution_order:
            downstream_is_batch = any(
                self._jobs[child].task_spec.batch for child in graph.successors(name)
            )
            job = self._jobs[name]
            if job.task_spec.batch and job.task_spec.dependencies:
                dependency = job.task_spec.dependencies[0]
                if not self._jobs[dependency].task_spec.batch:
                    raise ValueError(
                        f"batch task '{name}' must depend on a batch task",
                    )
            if (job.task_spec.batch or downstream_is_batch) and graph.out_degree(
                name
            ) != 1:
                raise ValueError(
                    f"batch stream from job '{name}' must have exactly one "
                    "downstream consumer",
                )
        return execution_order

    def _build_graph(self) -> nx.DiGraph[str]:
        """Build the dependency graph for registered jobs.

        Returns:
            A directed graph of job dependencies.
        """
        graph: nx.DiGraph[str] = nx.DiGraph()
        graph.add_nodes_from(self._jobs)

        for name, job in self._jobs.items():
            for dependency in job.task_spec.dependencies:
                if dependency not in self._jobs:
                    raise ValueError(
                        f"job '{name}' depends on unknown job '{dependency}'",
                    )
                graph.add_edge(dependency, name)

        return graph
