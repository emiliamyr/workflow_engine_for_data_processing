import pytest

from workflow_engine import retry, track_latency


def test_track_latency_preserves_result_and_records_latency() -> None:
    @track_latency
    def add(left: int, right: int) -> int:
        return left + right

    assert add(2, 3) == 5
    assert add.last_latency is not None
    assert add.last_latency >= 0


def test_track_latency_records_latency_when_function_fails() -> None:
    @track_latency
    def fail() -> None:
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        fail()

    assert fail.last_latency is not None


def test_retry_retries_selected_exception() -> None:
    attempts = 0

    @retry(max_attempts=3, exceptions=(ValueError,))
    def eventually_succeeds() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("not yet")
        return "done"

    assert eventually_succeeds() == "done"
    assert attempts == 3


def test_retry_raises_after_max_attempts() -> None:
    attempts = 0

    @retry(max_attempts=2, exceptions=(ValueError,))
    def always_fails() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError("failed")

    with pytest.raises(ValueError, match="failed"):
        always_fails()
    assert attempts == 2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_attempts": 0}, "max_attempts"),
        ({"delay": -1}, "delay"),
        ({"exceptions": ()}, "exceptions"),
    ],
)
def test_retry_rejects_invalid_configuration(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        retry(**kwargs)  # type: ignore[arg-type]
