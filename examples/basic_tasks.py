"""Basic example of defining and using workflow tasks."""

from workflow_engine import task


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
    users = extract_users()
    print(users)
    active_users = filter_active(users)

    print(active_users)
    print(filter_active.task_spec)
