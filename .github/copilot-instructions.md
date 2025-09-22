# Guide Copilot pour ce projet

## Aperçu rapide
Projet Python packagé avec Flit, orchestré par tox + tox-uv. L’environnement local est géré en `.venv` via `tox --devenv`. Qualité: Ruff (lint/format), mypy (types), pytest (tests+cov). Automatisations via Justfile et pre-commit. Docs avec MkDocs (base minimale).

## Logique de travail et outils
- Création/activation de l’environnement via `.envrc` et `direnv` (automatisation locale).
- Initialisation avec `just devenv`: crée/synchronise `.venv` via `tox --devenv -e devenv` (tox-uv lit `[dependency-groups]`) et installe pre-commit.
- Tâches centralisées via le `Justfile` (build, test, lint, types, docs, release).
- Orchestration multi-environnements avec `tox` (local et CI), gestion des dépendances avec `uv` (rapide, moderne, compatible PEP).
- Packaging et distribution avec `flit`.

## Tâches du quotidien
- Tests: `tox -e tests` (couverture minimale 80%, rapport des lignes manquantes en terminal).
- Typage: `tox -e typing` (mypy strict sur package + tests; configuration dans `pyproject.toml`).
- Lint/format: `pre-commit run ruff --all-files` et `pre-commit run ruff-format --all-files`.
- Docs: `tox -e docs` (build) et `just serve-docs` (serveur local si besoin).
- Sécurité: `tox -e security` (bandit + safety, best-effort).
- Tout exécuter d’un coup: `just check` (alias `tox`).

## Dépendances et configuration
- Runtime: `[project.dependencies]` dans `pyproject.toml`.
- Dev: groupes `[dependency-groups]` — `dev`, `typing`, `tests`, `docs`, `security`.
- Tox-uv synchronise ces groupes selon l’environnement via `dependency_groups = ...` dans `tox.ini`.

## Consignes Copilot
- Respecter la structure du template (code source, tests, config) et la séparation des modules.
- Prévoir l’extensibilité (points d’entrée CLI, interfaces abstraites quand pertinent).
- Utiliser uniquement les dépendances listées dans `pyproject.toml` en les plaçant dans le bon groupe.
- Générer du code moderne, typé (type hints) et documenté (docstrings concises).
- Proposer des tests Pytest pour toute nouvelle fonctionnalité (happy path + 1–2 cas limites).
- Toujours utiliser des espaces (4) pour l’indentation Python; les tabulations sont interdites.

## Rappels CI/CD
- CI exécute automatiquement les environnements tox via tox-gh; caches pip/uv/.tox activés et utilisation de `setup-uv`.
- Build d’artefacts via `tox -e build` (environnement dédié, hors envlist par défaut).
- Versioning/Release: Conventional Commits requis; `cz bump` met à jour la version (`pyproject.toml` + `__init__.py`).

## Fichiers et commandes clés
- `pyproject.toml`: metadata, dependency-groups, configuration des outils (ruff, mypy, commitizen).
- `tox.ini`: mapping des environnements vers les `dependency_groups` (tests, typing, precommit, docs, security, devenv).
- `Justfile`: recettes (env, tests, types, lint/format, docs, build via `tox -e build`, release via Commitizen).
- `tests/test_packaging_attribute.py`: vérifie `__version__` (PEP 440) et la description du package.
- `mkdocs.yml` et `docs/` pour la documentation.

Conseil: adaptez les propositions aux conventions établies (dependency-groups, tox-uv, pre-commit). Conservez la cohérence Ruff/mypy et évitez toute régression de couverture (<80%).
