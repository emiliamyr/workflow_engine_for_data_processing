from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import ParamSpec, TypeVar, overload

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Basic metadata describing a workflow task."""

    name: str
    dependencies: tuple[str, ...]


class Task[**P, R]:
    """Wrapper attaching TaskSpec metadata to a function."""

    def __init__(
        self,
        func: Callable[P, R],
        name: str | None = None,
        depends_on: tuple[str, ...] = (),
    ) -> None:
        self.func = func
        self.task_spec = TaskSpec(
            name=name or func.__name__,
            dependencies=depends_on,
        )
        functools.update_wrapper(self, func)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)


@overload
def task[**P, R](function: Callable[P, R]) -> Task[P, R]: ...


@overload
def task[**P, R](
    function: None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Callable[[Callable[P, R]], Task[P, R]]: ...


def task[**P, R](
    function: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Task[P, R] | Callable[[Callable[P, R]], Task[P, R]]:
    """Decorator supporting both @task and @task(...) syntax."""

    def decorate(func: Callable[P, R]) -> Task[P, R]:
        return Task(func, name=name, depends_on=depends_on)

    if function is None:
        return decorate

    if callable(function):
        return decorate(function)

    return decorate
