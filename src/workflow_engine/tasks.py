from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Basic metadata describing a workflow task."""

    name: str
    dependencies: tuple[str, ...]


def task(
    function: Any = None,
    *,
    name: str | None = None,
    depends_on: tuple[str, ...] = (),
) -> Any:
    """Mark a function as a workflow task."""

    def decorate(func: Any) -> Any:
        spec = TaskSpec(
            name=name or func.__name__,
            dependencies=depends_on,
        )

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        wrapper.task_spec = spec
        return wrapper

    if function is None:
        return decorate
    return decorate(function)
