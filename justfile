set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

_prepare-artifacts:
    @powershell -Command "if (!(Test-Path .artifacts)) { New-Item -ItemType Directory -Path .artifacts | Out-Null }"

install:
    uv sync --all-groups

lock:
    uv lock

lint: _prepare-artifacts
    uv run ruff check src tests examples
    uv run ruff format --check src tests examples

fix: _prepare-artifacts
    uv run ruff format src tests examples
    uv run ruff check --fix src tests examples

typecheck: _prepare-artifacts
    uv run pyright

test: _prepare-artifacts
    uv run pytest --cov=src/workflow_engine --cov-report=html:.artifacts/htmlcov --cov-report=xml:.artifacts/coverage.xml

example file:
    uv run python examples/{{file}}

check: lint typecheck test

clean:
    Remove-Item -Recurse -Force .artifacts, output -ErrorAction SilentlyContinue