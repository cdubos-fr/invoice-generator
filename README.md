[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Générateur de facture et devis

Application Python (PyQt6) pour créer des devis et générer des factures, avec export PDF et JSON. Architecture MVC propre, configuration fichier, et qualité outillée (ruff, mypy, pytest).

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

## Utilisation (CLI)

Après installation, lancez l’application:

```bash
invoice-generator
```

L’UI propose 3 onglets: Devis, Facture, Configuration. Vous pouvez:
- créer des lignes (produits/services), appliquer des remises,
- importer un devis JSON dans l’onglet Facture (bouton « Importer depuis devis JSON »),
- générer un document (PDF + JSON).

## Format JSON des documents

Les fichiers exportés contiennent notamment:

```json
{
	"type": "quote|invoice",
	"number": "FAC-2025-0001",
	"date": "2025-01-15",
	"issuer": {"name": "Ma Société"},
	"customer": {"name": "Client SA"},
	"lines": [
		{
			"item_key": "svc",
			"description": "Service",
			"quantity": 2,
			"unit_price": 100.0,
			"discount_pct": 10.0,
			"total_ht": 180.0
		}
	],
	"subtotal_ht": 180.0
}
```

Le parseur d’import de devis est permissif mais ignore les lignes mal formées (sans `item_key`, `description`, `quantity`, `unit_price`). Le champ `discount_pct` manquant est considéré comme `0.0`.

## PDF

Le PDF généré inclut:
- entête (type/numéro, date, émetteur, client, logo optionnel),
- tableau des lignes paginé,
- sous-total HT,
- notes optionnelles,
- pied de page avec pagination.

### Logo de la société

Vous pouvez configurer un logo affiché en haut à droite:
- Onglet « Configuration » → champ « Logo » pour sélectionner un fichier PNG/JPG.
- « Largeur logo (px) » et « Hauteur logo (px) » définissent la taille maximale (ratio conservé).
- « Marge droite logo (px) » règle l’écart au bord droit.
- Un aperçu est visible et se met à jour en temps réel.

Notes:
- Le fichier de configuration est stocké par défaut dans `~/.config/invoice-generator/config.json`.
- Clés utilisées: `company.logo_path`, `company.logo_max_width`, `company.logo_max_height`, `company.logo_margin_right` (floats, en pixels).

## Développement

Voir `Justfile`, `tox.ini` et `pyproject.toml` pour les recettes (tests, lint/format, types, docs, sécurité). Utilisez `just check` pour lancer la batterie complète via tox.
```
