import logging
import runpy
import sys
from pathlib import Path

import pytest

from workflow_engine.cli import main


def _write_workflow(path: Path) -> None:
    path.write_text(
        """\
from workflow_engine import Pipeline, task

@task
def extract():
    return 40

@task(depends_on=("extract",))
def total(value):
    return value + 2

def build_pipeline():
    pipeline = Pipeline()
    pipeline.add(total)
    pipeline.add(extract)
    return pipeline
""",
        encoding="utf-8",
    )


def test_cli_run_displays_graph_logs_status_and_durations(
    tmp_path: Path,
    capsys,
    caplog,
) -> None:
    workflow = tmp_path / "workflow.py"
    _write_workflow(workflow)

    with caplog.at_level(logging.INFO):
        assert main(["run", str(workflow)]) == 0

    output = capsys.readouterr().out
    assert "Dependency graph:" in output
    assert "extract -> total" in output
    assert "Pipeline succeeded" in output
    assert "succeeded: extract" in output
    assert "succeeded: total" in output
    assert "Starting task extract" in caplog.text
    assert "Finished task total" in caplog.text


def test_cli_graph_displays_workflow_without_running_tasks(
    tmp_path: Path,
    capsys,
) -> None:
    workflow = tmp_path / "workflow.py"
    _write_workflow(workflow)

    assert main(["graph", str(workflow)]) == 0

    output = capsys.readouterr().out
    assert "extract (start)" in output
    assert "extract -> total" in output
    assert "Pipeline succeeded" not in output


def test_cli_reports_workflow_execution_failure(
    tmp_path: Path,
    capsys,
    caplog,
) -> None:
    workflow = tmp_path / "workflow.py"
    workflow.write_text(
        """\
from workflow_engine import Pipeline, task

@task
def fail():
    raise ValueError("broken task")

def build_pipeline():
    pipeline = Pipeline()
    pipeline.add(fail)
    return pipeline
""",
        encoding="utf-8",
    )

    with caplog.at_level(logging.INFO):
        assert main(["run", str(workflow)]) == 1

    assert "Pipeline failed" in capsys.readouterr().out
    assert "Workflow execution failed" in caplog.text


def test_cli_rejects_workflow_without_builder(
    tmp_path: Path,
    caplog,
) -> None:
    workflow = tmp_path / "workflow.py"
    workflow.write_text("value = 1\n", encoding="utf-8")

    with caplog.at_level(logging.INFO):
        assert main(["graph", str(workflow)]) == 2

    assert "must define build_pipeline()" in caplog.text


def test_cli_rejects_missing_workflow_file(
    tmp_path: Path,
    caplog,
) -> None:
    workflow = tmp_path / "missing.py"

    with caplog.at_level(logging.INFO):
        assert main(["graph", str(workflow)]) == 2

    assert "workflow file does not exist" in caplog.text


def test_cli_rejects_builder_returning_non_pipeline(
    tmp_path: Path,
    caplog,
) -> None:
    workflow = tmp_path / "workflow.py"
    workflow.write_text(
        "def build_pipeline():\n    return object()\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.INFO):
        assert main(["graph", str(workflow)]) == 2

    assert "build_pipeline() must return a Pipeline" in caplog.text


def test_module_entrypoint_runs_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workflow = tmp_path / "workflow.py"
    _write_workflow(workflow)
    monkeypatch.setattr(sys, "argv", ["workflow-engine", "graph", str(workflow)])

    with pytest.raises(SystemExit, match="0"):
        runpy.run_module("workflow_engine.__main__", run_name="__main__")
