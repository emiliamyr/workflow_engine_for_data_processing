set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

# Show available commands
default:
    @just --list

# Create the artifacts directory
_prepare-artifacts:
    @uv run python -c "from pathlib import Path; Path('.artifacts').mkdir(exist_ok=True)"

# Install project dependencies
install:
    uv sync --all-groups

# Update the lockfile
lock:
    uv lock

# Check formatting and lint rules
lint: _prepare-artifacts
    uv run ruff check src tests examples
    uv run ruff format --check src tests examples

# Format code and fix lint issues
fix: _prepare-artifacts
    uv run ruff format src tests examples
    uv run ruff check --fix src tests examples

# Run type checking
typecheck: _prepare-artifacts
    uv run pyright

# Run the test suite with coverage
test: _prepare-artifacts
    uv run pytest --cov=src/workflow_engine --cov-report=html:.artifacts/htmlcov --cov-report=xml:.artifacts/coverage.xml

# Run an example script
example file:
    uv run python examples/{{file}}

# Run linting, type checking, and tests
check: lint typecheck test

# Remove generated artifacts and output
clean:
    @powershell -Command "try { Remove-Item -Recurse -Force .artifacts, output -ErrorAction Stop } catch {}; exit 0"