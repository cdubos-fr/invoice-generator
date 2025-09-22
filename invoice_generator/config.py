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
        'logo_max_width': 60.0,
        'logo_max_height': None,
        'logo_margin_right': 20.0,
        'address': None,
        'email': None,
        'phone': None,
        'siret': None,
    },
    'counters': {
        'quote': 0,
        'invoice': 0,
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

    def set_company_logo_path(self, logo_path: str | None) -> None:
        """Update the company logo path and save the configuration."""
        data = self.load()
        data.setdefault('company', {})['logo_path'] = logo_path
        self.save(data)

    def set_company_logo_max_width(self, width: float | None) -> None:
        """Update the company logo maximum width in pixels (float)."""
        data = self.load()
        data.setdefault('company', {})['logo_max_width'] = width
        self.save(data)

    def set_company_logo_max_height(self, height: float | None) -> None:
        """Update the company logo maximum height in pixels (float)."""
        data = self.load()
        data.setdefault('company', {})['logo_max_height'] = height
        self.save(data)

    def set_company_logo_margin_right(self, margin: float | None) -> None:
        """Update the right margin (pixels) used to offset the logo from the page border."""
        data = self.load()
        data.setdefault('company', {})['logo_margin_right'] = margin
        self.save(data)

    # Coordonnées société
    def set_company_address(self, address: str | None) -> None:
        """Update company postal address (optional)."""
        data = self.load()
        data.setdefault('company', {})['address'] = address
        self.save(data)

    def set_company_email(self, email: str | None) -> None:
        """Update company email (optional)."""
        data = self.load()
        data.setdefault('company', {})['email'] = email
        self.save(data)

    def set_company_phone(self, phone: str | None) -> None:
        """Update company phone (optional)."""
        data = self.load()
        data.setdefault('company', {})['phone'] = phone
        self.save(data)

    def set_company_siret(self, siret: str | None) -> None:
        """Update company SIRET identifier (optional)."""
        data = self.load()
        data.setdefault('company', {})['siret'] = siret
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

    def delete_item(self, key: str) -> None:
        """Delete an item by its key if it exists."""
        data = self.load()
        items = data.setdefault('items', [])
        new_items = [it for it in items if it.get('key') != key]
        if len(new_items) != len(items):
            data['items'] = new_items
            self.save(data)

    # Numérotation documents
    def next_number(self, doc_type: str, prefix: str = '', width: int = 4) -> str:
        """Return next incremental number for given doc type and persist the counter.

        doc_type should be 'quote' or 'invoice'.
        """
        data = self.load()
        counters = data.setdefault('counters', {'quote': 0, 'invoice': 0})
        counters[doc_type] = int(counters.get(doc_type, 0)) + 1
        self.save(data)
        num = counters[doc_type]
        return f'{prefix}{num:0{width}d}'
