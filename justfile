set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

default:
    @just --list

install:
    uv sync

lock:
    uv lock

test:
    uv run pytest

clean:
    Remove-Item -Recurse -Force output -ErrorAction SilentlyContinue
