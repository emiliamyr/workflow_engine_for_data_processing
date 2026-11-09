"""Task wrappers and task decorators."""

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
        """Initialize a task wrapper.

        Args:
            func: Function executed by the task.
            name: Optional task name.
            depends_on: Names of prerequisite tasks.
        """
        self.func = func
        self.task_spec = TaskSpec(
            name=name or func.__name__,
            dependencies=depends_on,
        )
        functools.update_wrapper(self, func)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Execute the wrapped task function.

        Args:
            *args: Positional arguments for the task function.
            **kwargs: Keyword arguments for the task function.

        Returns:
            The task function's result.
        """
        return self.func(*args, **kwargs)


@overload
def task[**P, R](function: Callable[P, R]) -> Task[P, R]:
    """Decorate a function as a task.

    Args:
        function: Function to wrap.

    Returns:
        A configured task wrapper.
    """
    ...


@overload
def task[**P, R](
    function: None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Callable[[Callable[P, R]], Task[P, R]]:
    """Decorate a function as a task.

    Args:
        function: Function to wrap.
        name: Optional task name.
        depends_on: Names of prerequisite tasks.

    Returns:
        A decorator returning a task wrapper.
    """
    ...


def task[**P, R](
    function: Callable[P, R] | None = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Task[P, R] | Callable[[Callable[P, R]], Task[P, R]]:
    """Decorate a function as a task.

    Args:
        function: Function to wrap, when using ``@task``.
        name: Optional task name.
        depends_on: Names of prerequisite tasks.

    Returns:
        A task wrapper or a decorator returning one.
    """

    def decorate(func: Callable[P, R]) -> Task[P, R]:
        """Wrap a function with task metadata.

        Args:
            func: Function to wrap.

        Returns:
            The configured task wrapper.
        """
        return Task(func, name=name, depends_on=depends_on)

    if function is None:
        return decorate

    if callable(function):
        return decorate(function)

    return decorate
