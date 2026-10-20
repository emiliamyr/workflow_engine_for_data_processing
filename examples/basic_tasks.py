"""Basic example of defining and using workflow tasks."""

from workflow_engine import task


@task
def say_hello(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"


@task(name="extract_users")
def extract_users() -> list[dict[str, object]]:
    """Return source records."""
    return [
        {"name": "Ada", "active": True},
        {"name": "Grace", "active": False},
    ]


@task(name="filter_active", depends_on=("extract_users",))
def filter_active(users: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep only active users."""
    return [user for user in users if user["active"]]


if __name__ == "__main__":
    print(extract_users.task_spec)
    print(filter_active.task_spec)
    print(say_hello.task_spec)

    users = extract_users()
    active_users = filter_active(users)
    greeting = say_hello("Ada")

    print(users)
    print(active_users)
    print(greeting)
