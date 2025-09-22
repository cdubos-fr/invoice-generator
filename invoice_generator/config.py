"""Gestion de la configuration (fichier JSON).

Stocke: société émettrice, logo, et les items (produits/services) avec prix par défaut.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_CONFIG: dict[str, Any] = {
    'company': {
        'name': 'Ma Société',
        'logo_path': None,
        'address': None,
        'email': None,
        'phone': None,
    },
    'items': [
        {'key': 'service', 'label': 'Service', 'unit_price': 80.0},
        {'key': 'product', 'label': 'Produit', 'unit_price': 50.0},
    ],
}


@dataclass(slots=True)
class ConfigManager:
    """Gestionnaire simple de configuration sur fichier JSON."""

    path: Path

    def load(self) -> dict[str, Any]:
        """Return the current config dict from disk or defaults if missing."""
        if not self.path.exists():
            return DEFAULT_CONFIG.copy()
        import json

        with self.path.open('r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data: dict[str, Any]) -> None:
        """Persist the given config dict to disk (UTF-8, pretty)."""
        import json

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Helpers typed
    def get_company(self) -> dict[str, Any]:
        """Return the company sub-config."""
        return self.load()['company']

    def set_company_name(self, name: str) -> None:
        """Update the company name and save the configuration."""
        data = self.load()
        data.setdefault('company', {})['name'] = name
        self.save(data)

    def list_items(self) -> list[dict[str, Any]]:
        """Return the list of configured items (products/services)."""
        return list(self.load().get('items', []))

    def upsert_item(self, key: str, label: str, unit_price: float) -> None:
        """Insert or update an item by key."""
        data = self.load()
        items = data.setdefault('items', [])
        for it in items:
            if it.get('key') == key:
                it['label'] = label
                it['unit_price'] = unit_price
                self.save(data)
                return
        items.append({'key': key, 'label': label, 'unit_price': unit_price})
        self.save(data)
