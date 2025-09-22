[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Générateur de facture et devis

# Installation

```bash
pip install <path-to-this-project>
```
or
```bash
pip install git+<git-url>
```

to install it in editable mode:
```bash
pip install -e .
```

to add developpement dependencies:
```bash
pip install -e ".[dev]"
```

# Setup dev environment

Recommended: use the Just recipe (tox-uv will sync dependency groups into .venv)

```bash
just devenv
```

Manual alternative with uv

```bash
uv venv .venv
source .venv/bin/activate
uv pip install --upgrade pip
uv pip install -e ".[dev,typing,tests,docs,security]"
pre-commit install
```

Or manual with pip (fallback)

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,typing,tests,docs,security]"
pre-commit install
```

# Build (sdist & wheel)

```bash
python -m build
```

# Run tests

```bash
pytest
```

# Type checking

```bash
mypy -p invoice_generator
```

# Docs

```bash
mkdocs build
```
