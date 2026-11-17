"""Command-line interface for running workflow pipelines."""

import argparse
import asyncio
import importlib.util
import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

from workflow_engine import Pipeline

logger = logging.getLogger(__name__)


def _load_pipeline(path: Path) -> Pipeline:
    """Load a pipeline returned by a workflow module's ``build_pipeline``.

    Args:
        path: Python file containing a ``build_pipeline()`` function.

    Returns:
        The pipeline built by the workflow module.
    """
    workflow_path = path.resolve()
    if not workflow_path.is_file():
        raise FileNotFoundError(f"workflow file does not exist: {workflow_path}")

    module_name = f"_workflow_engine_workflow_{workflow_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, workflow_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load workflow file: {workflow_path}")

    module: ModuleType = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    sys.path.insert(0, str(workflow_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
        sys.modules.pop(module_name, None)

    build_pipeline = getattr(module, "build_pipeline", None)
    if not callable(build_pipeline):
        raise AttributeError(
            f"workflow module must define build_pipeline(): {workflow_path}",
        )

    pipeline = build_pipeline()
    if not isinstance(pipeline, Pipeline):
        raise TypeError("build_pipeline() must return a Pipeline")
    return pipeline


def _print_graph(pipeline: Pipeline) -> None:
    """Print the tasks and their direct prerequisite edges."""
    print("Dependency graph:")
    for task_name, dependencies in pipeline.dependency_graph().items():
        if dependencies:
            print(f"  {', '.join(dependencies)} -> {task_name}")
        else:
            print(f"  {task_name} (start)")


def _print_report(pipeline: Pipeline) -> None:
    """Print the last run's status and per-task execution times."""
    report = pipeline.last_report
    if report is None:
        raise RuntimeError("pipeline has no execution report")

    print(
        f"Pipeline {report.status} in {report.duration_seconds:.3f} seconds",
    )
    for task in report.tasks:
        duration = (
            "not run"
            if task.duration_seconds is None
            else f"{task.duration_seconds:.3f} seconds"
        )
        print(f"  {task.status}: {task.name} ({duration})")
        if task.error:
            print(f"    {task.error}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run a workflow CLI command.

    Args:
        argv: Optional command-line arguments, primarily for testing.

    Returns:
        The process exit code.
    """
    parser = argparse.ArgumentParser(prog="workflow-engine")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("graph", "run"):
        command_parser = commands.add_parser(
            command,
            help=(
                f"{'show the dependency graph for' if command == 'graph' else 'run'} "
                "a workflow"
            ),
        )
        command_parser.add_argument(
            "workflow",
            type=Path,
            help="Python file defining build_pipeline()",
        )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stdout,
    )

    try:
        pipeline = _load_pipeline(args.workflow)
        _print_graph(pipeline)
        if args.command == "graph":
            return 0

        try:
            asyncio.run(pipeline.run_async())
        except asyncio.CancelledError:
            logger.error("Workflow execution was cancelled")
            _print_report(pipeline)
            return 1
        except Exception:
            logger.exception("Workflow execution failed")
            _print_report(pipeline)
            return 1

        _print_report(pipeline)
        return 0
    except Exception:
        logger.exception("Could not prepare workflow")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
