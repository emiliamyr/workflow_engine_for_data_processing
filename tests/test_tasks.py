from workflow_engine.tasks import TaskSpec, task


def test_task_keeps_function_callable_and_stores_metadata() -> None:
    @task
    def extract() -> list[dict[str, int]]:
        return [{"value": 1}]

    assert extract() == [{"value": 1}]
    assert extract.task_spec == TaskSpec("extract", ())


def test_task_accepts_name_and_dependencies() -> None:
    @task(name="clean_data", depends_on=("extract_data",))
    def clean() -> str:
        return "done"

    assert clean() == "done"
    assert clean.task_spec.name == "clean_data"
    assert clean.task_spec.dependencies == ("extract_data",)
