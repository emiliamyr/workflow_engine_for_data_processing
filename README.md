# Workflow Engine

A lightweight Python workflow engine for building and executing data-processing
pipelines.

The project currently provides tested base pipeline components, task metadata,
retry and latency utilities, and a dependency-aware pipeline.

## Planned Features

- Extract, transform, and load components.
- Dependency-aware directed acyclic graph (DAG) execution.
- Batch processing with generators.
- Parallel execution of independent tasks with `asyncio`.
- Abstract base classes and reusable component interfaces.
- Retry and latency-tracking decorators.
- Execution metrics and workflow monitoring.
- Command-line interface for running workflows and viewing results.

## Technology Stack

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management.
- `asyncio` for asynchronous execution.
- `networkx` for dependency graphs.
- `pytest` for testing.
- `pandas`, `numpy`, and `polars` for data processing.

## Project Structure

```text
.
├── .gitignore                # Ignored local and generated files
├── .python-version           # Project Python version
├── examples/
│   ├── basic_pipeline.py    # Manual pipeline example
│   ├── basic_tasks.py       # Task decorator example
│   └── utilities.py         # Retry and latency decorators example
├── src/
│   └── workflow_engine/
│       ├── __init__.py       # Package entry point
│       ├── base.py           # Base extractor, transformer, and loader classes
│       ├── components.py     # Simple in-memory pipeline components
│       ├── decorators.py     # Retry and latency decorators
│       ├── pipeline.py       # Dependency-aware pipeline execution
│       └── tasks.py          # Basic task decorator and metadata
├── tests/
│   ├── test_structure.py     # Project structure test
│   ├── test_base.py          # Base component tests
│   ├── test_components.py    # In-memory pipeline tests
│   ├── test_decorators.py    # Retry and latency decorator tests
│   ├── test_pipeline.py      # Pipeline graph and execution tests
│   └── test_tasks.py         # Task decorator tests
├── justfile                  # Common development commands
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Locked dependency versions
└── README.md                 # Project documentation
```

## Setup

The project uses Python 3.14, selected through `.python-version`.

```bash
just install
```

The `just install` recipe runs `uv sync`, which creates or updates the virtual
environment and installs the dependencies from `uv.lock`.

To refresh the dependency lockfile manually:

```bash
just lock
```

The equivalent direct `uv` commands are `uv sync` and `uv lock`.

## Development Commands

The project uses [Just](https://just.systems/) as a command runner:

```bash
just install
just lock
just test
just example
just clean
```

Run an example file with:

```bash
just example basic_tasks.py
```

The file path is required. The command is equivalent to:

```bash
uv run python examples/basic_tasks.py
```

The `basic_pipeline.py` example demonstrates the current manual pipeline.
The `pipeline.py` example demonstrates dependency-aware job execution.

The CI checks can be run locally with:

```bash
just check
```

GitHub Actions runs this command for pushes to `master` and pull requests
targeting `master`. Successful checks also trigger a SonarCloud scan when the
`SONAR_TOKEN` repository secret is available.

## Base Pipeline Components

The first pipeline building blocks are independent abstract base classes:

```text
BaseExtractor
BaseTransformer
BaseLoader
```

## Simplest Analogy

- `BaseExtractor` — where do we get the data from?
- `BaseTransformer` — what do we change in the data?
- `BaseLoader` — where do we save the data?

The base classes define the expected interface. Concrete CSV, SQL, cleaning,
and JSON components will implement these interfaces in later stages.

The first concrete components are intentionally simple:

- `InMemoryExtractor` reads records supplied as a Python iterable.
- `SelectColumnsTransformer` keeps selected fields in each record.
- `ListLoader` collects transformed records in a Python list.

They demonstrate the first manual pipeline without a graph:

```python
from workflow_engine import (
    InMemoryExtractor,
    ListLoader,
    SelectColumnsTransformer,
)

extractor = InMemoryExtractor(
    [{"name": "Ada", "active": True}],
)
transformer = SelectColumnsTransformer(["name"])
loader = ListLoader()

batches = extractor.extract(batch_size=100)
transformed = (transformer.transform(batch) for batch in batches)
result = loader.load(transformed)
```

Run the example with:

```bash
just example basic_pipeline.py
```

## Utilities

The package exports two reusable decorators:

- `@track_latency` measures the last execution time in seconds.
- `@retry` repeats a function for selected exceptions.

Run the utilities example with:

```bash
just example utilities.py
```

## Dependency-Aware Pipelines

Jobs are declared with `@job`, added to a `Pipeline`, and connected through
their `depends_on` metadata. The pipeline builds a directed acyclic graph and
executes jobs in topological order. A job receives the results of its
dependencies as positional arguments.

```python
from workflow_engine import Pipeline, job


@job
def extract() -> list[int]:
    return [1, 2, 3]


@job(depends_on=("extract",))
def total(values: list[int]) -> int:
    return sum(values)


pipeline = Pipeline()
pipeline.add(total)
pipeline.add(extract)
results = pipeline.run()
```

`results` contains the result of every job by name. The pipeline rejects
unknown dependencies, duplicate job names, and cyclic dependencies.

Run the example with:

```bash
just example pipeline.py
```

## Development Plan

### 1. Base Architecture and Data Streaming — Complete

Create `BaseExtractor`, `BaseTransformer`, and `BaseLoader` using abstract base
classes. Add batch-oriented processing based on generators and `yield`.

The current implementation includes in-memory components and a tested manual
pipeline.

### 2. Dependency-Aware Pipeline

Complete: add `@job`, `Pipeline.add()`, dependency graph construction, DAG
validation, topological execution, and result passing between dependent jobs.

### 3. Data Components

Add reusable CSV and SQL extractors, data-cleaning and filtering transformers,
and JSON or database loaders.

### 4. Workflow Engine

The first synchronous dependency-aware `Pipeline` implementation is complete.
Future work includes richer component integration, parallel execution through
`asyncio`, and execution metrics.

### 5. Testing and CLI Demo

Add unit and integration tests with `pytest`, then create a CLI demo that runs
workflows and displays logs, execution times, and pipeline status.

## License

This project is currently intended for educational and demonstration purposes.
