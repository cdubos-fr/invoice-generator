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

### Logo

Dans l’onglet Configuration:
- sélectionnez un fichier image (PNG/JPG) comme logo,
- ajustez « Largeur logo (px) » et « Hauteur logo (px) » pour forcer une taille max (ratio conservé),
- ajustez « Marge droite logo (px) » pour l’écart entre le logo et le bord droit,
- observez l’aperçu dynamique.

Les valeurs sont enregistrées dans le fichier de configuration utilisateur et appliquées lors de la génération du PDF.

## Qualité

Tests via pytest, lint/format avec Ruff, typage mypy. Utilisez `just check` pour tout lancer via tox.
