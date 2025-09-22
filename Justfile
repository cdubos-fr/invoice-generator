set shell := ["zsh", "-uc"]

default:
    @just --list

devenv:
    @echo "Setting up development environment with tox-uv (.venv)"
    @tox devenv -e devenv .venv
    @source .venv/bin/activate; pre-commit install || true
    @echo "✓ Development environment ready"

# Run all checks
check:
    @tox

# Run tests
test:
    @tox -e tests

# Run type checking
typecheck:
    @tox -e typing

# Format code
format:
    @pre-commit run ruff-format --all-files

# Lint code
lint:
    @pre-commit run ruff --all-files

docs:
    @tox -e docs

serve-docs:
    @mkdocs serve

clean:
    @find . -type d -name .venv -exec rm -rf {} +
    @find . -type d -name __pycache__ -exec rm -rf {} +
    @find . -type d -name .ruff_cache -exec rm -rf {} +
    @find . -type d -name dist -exec rm -rf {} +
    @find . -type d -name build -exec rm -rf {} +
    @find . -type d -name .pytest_cache -exec rm -rf {} +
    @find . -type d -name "*.egg-info" -exec rm -rf {} +
    @find . -type d -name .mypy_cache -exec rm -rf {} +
    @find . -type d -name .tox -exec rm -rf {} +
    @find . -type d -name site -exec rm -rf {} +
    @find . -type f -name .coverage -exec rm -rf {} +
    @find . -type d -name result -exec rm -rf {} +

build:
    @tox -e build

update-deps:
    @echo "Recreating dev environment with tox-uv (fresh deps)"
    @tox --recreate devenv -e devenv .venv

sync:
    @echo "Syncing dev environment with tox-uv"
    @tox devenv -e devenv .venv

release version:
    @cz bump
    @just build
