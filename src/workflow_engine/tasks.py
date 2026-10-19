"""Task definition utilities and metadata structures."""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, cast, overload


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Basic metadata describing a workflow task.

    Attributes:
        name: The unique identifier or descriptive name of the task.
        dependencies: Task names that must complete before execution.
    """

    name: str
    dependencies: tuple[str, ...]


class TaskCallable[**P, R_co](Protocol):
    """Protocol for callables that have task metadata attached."""

    task_spec: TaskSpec

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


@overload
def task[**P, R](function: Callable[P, R], /) -> TaskCallable[P, R]: ...


@overload
def task[**P, R](
    function: None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Callable[[Callable[P, R]], TaskCallable[P, R]]: ...


def task[**P, R](
    function: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> TaskCallable[P, R] | Callable[[Callable[P, R]], TaskCallable[P, R]]:
    """Mark a callable function as a workflow task.

    Args:
        function: Target function to wrap as a workflow task.
        name: Optional custom name for the task.
        depends_on: Tuple of task names this task depends on.

    Returns:
        TaskCallable or decorator function attached with task metadata.
    """

    def decorate(func: Callable[P, R]) -> TaskCallable[P, R]:
        spec = TaskSpec(
            name=name or func.__name__,
            dependencies=depends_on,
        )

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        task_wrapper = cast(TaskCallable[P, R], wrapper)
        task_wrapper.task_spec = spec
        return task_wrapper

    if function is None:
        return decorate
    return decorate(function)
