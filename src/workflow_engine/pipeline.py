"""Dependency-aware execution of decorated workflow jobs."""

import networkx as nx

from workflow_engine.tasks import Task


class Pipeline:
    """Build and execute a directed acyclic graph of jobs."""

    def __init__(self) -> None:
        """Initialize an empty pipeline."""
        self._jobs: dict[str, Task] = {}

    def add(self, job: Task) -> None:
        """Add a uniquely named job to the pipeline.

        Args:
            job: Task to add.
        """
        name = job.task_spec.name
        if name in self._jobs:
            raise ValueError(f"job already added: {name}")
        self._jobs[name] = job

    def run(self) -> dict[str, object]:
        """Execute jobs in dependency order.

        Returns:
            Results keyed by job name.
        """
        graph = self._build_graph()
        results: dict[str, object] = {}

        try:
            execution_order = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("pipeline dependencies must be acyclic") from None

        for name in execution_order:
            job = self._jobs[name]
            dependency_results = [
                results[dependency] for dependency in job.task_spec.dependencies
            ]
            results[name] = job(*dependency_results)

        return results

    def _build_graph(self) -> nx.DiGraph[str]:
        """Build the dependency graph for registered jobs.

        Returns:
            A directed graph of job dependencies.
        """
        graph: nx.DiGraph[str] = nx.DiGraph()
        graph.add_nodes_from(self._jobs)

        for name, job in self._jobs.items():
            for dependency in job.task_spec.dependencies:
                if dependency not in self._jobs:
                    raise ValueError(
                        f"job '{name}' depends on unknown job '{dependency}'",
                    )
                graph.add_edge(dependency, name)

        return graph
