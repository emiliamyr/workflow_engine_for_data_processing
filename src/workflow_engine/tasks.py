from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, Protocol, TypeVar, cast, overload

P = ParamSpec("P")
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Basic metadata describing a workflow task."""

    name: str
    dependencies: tuple[str, ...]


class TaskFunction(Protocol[P, R_co]):
    task_spec: TaskSpec

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


@overload
def task[**P, R](
    function: Callable[P, R],
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> TaskFunction[P, R]: ...


@overload
def task[**P, R](
    function: None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Callable[[Callable[P, R]], TaskFunction[P, R]]: ...


def task[**P, R](
    function: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> TaskFunction[P, R] | Callable[[Callable[P, R]], TaskFunction[P, R]]:
    """Mark a function as a workflow task."""

    def decorate(func: Callable[P, R]) -> TaskFunction[P, R]:
        spec = TaskSpec(
            name=name or func.__name__,
            dependencies=depends_on,
        )

        @functools.wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        task_function = cast(TaskFunction[P, R], wrapped)
        task_function.task_spec = spec
        return task_function

    if function is None:
        return decorate
    return decorate(function)
