"""Reusable decorators for workflow functions."""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

_FIRST_ATTEMPT = 1
_NO_DELAY = 0.0


class LatencyFunction[**P, R]:
    """Callable wrapper exposing the last execution latency."""

    def __init__(self, function: Callable[P, R]) -> None:
        """Initialize a latency-tracking wrapper.

        Args:
            function: Callable whose execution should be measured.
        """
        self.function = function
        self.last_latency: float | None = None
        functools.update_wrapper(self, function)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """Call the wrapped function and record its latency.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            The wrapped function's result.
        """
        started_at = time.perf_counter()
        try:
            return self.function(*args, **kwargs)
        finally:
            self.last_latency = time.perf_counter() - started_at


def track_latency[**P, R](
    function: Callable[P, R],
) -> LatencyFunction[P, R]:
    """Decorate a function with latency tracking.

    Args:
        function: Callable whose execution should be measured.

    Returns:
        A callable wrapper exposing the last latency in seconds.
    """
    return LatencyFunction(function)


def retry(
    *,
    max_attempts: int = 3,
    delay: float = _NO_DELAY,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Create a decorator that retries selected failures.

    Args:
        max_attempts: Maximum number of calls.
        delay: Seconds to wait between attempts.
        exceptions: Exception types that trigger a retry.

    Returns:
        A decorator for retrying a callable.
    """

    if max_attempts < _FIRST_ATTEMPT:
        raise ValueError("max_attempts must be at least one")
    if delay < _NO_DELAY:
        raise ValueError("delay must not be negative")
    if not exceptions:
        raise ValueError("exceptions must not be empty")

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        """Wrap a function with the configured retry policy.

        Args:
            function: Callable to retry.

        Returns:
            The retrying wrapper.
        """

        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Call the function, retrying configured exceptions.

            Args:
                *args: Positional arguments for the wrapped function.
                **kwargs: Keyword arguments for the wrapped function.

            Returns:
                The wrapped function's result.
            """
            for attempt in range(_FIRST_ATTEMPT, max_attempts + _FIRST_ATTEMPT):
                try:
                    return function(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts:
                        raise
                    if delay:
                        time.sleep(delay)
            raise RuntimeError("retry attempts were exhausted")

        return wrapper

    return decorate
