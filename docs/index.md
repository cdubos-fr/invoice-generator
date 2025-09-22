---
title: Invoice Generator
---

# Invoice Generator

Application Python pour créer des devis et générer des factures, avec UI PyQt6 et exports PDF/JSON. L’architecture suit MVC et le projet est typé/testé.

## Démarrage

Après installation, lancez:

```
invoice-generator
```

Trois onglets:
- Devis: créer des lignes, appliquer des remises
- Facture: importer un devis JSON et finaliser
- Configuration: société et catalogue d’items

## Import d’un devis JSON

Dans l’onglet Facture, utilisez « Importer depuis devis JSON ». Le fichier attendu ressemble à:

```json
{
    "customer": {"name": "Client SA"},
    "lines": [
        {"item_key": "svc", "description": "Service", "quantity": 2, "unit_price": 100.0, "discount_pct": 10.0}
    ]
}
```

Le parseur ignore les lignes mal formées (clés requises manquantes). `discount_pct` manquant = `0.0`.

## PDF

Le PDF inclut entête (logo optionnel), tableau paginé, sous-total HT, notes et pagination.

## Qualité

Tests via pytest, lint/format avec Ruff, typage mypy. Utilisez `just check` pour tout lancer via tox.
