"""Modèles de domaine pour devis et factures.

Fournit des dataclasses modernes décrivant les entités manipulées par le backend (PDF/JSON)
et le frontend (UI PyQt6). Ces modèles sont agnostiques de l'interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING
from typing import Any


class DocumentType(StrEnum):
    """Type de document généré."""

    QUOTE = 'quote'
    INVOICE = 'invoice'


@dataclass(slots=True)
class Company:
    """Société émettrice du document."""

    name: str
    logo_path: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(slots=True)
class Party:
    """Tiers (client/destinataire) du document."""

    name: str
    address: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(slots=True)
class Item:
    """Produit ou service configuré, avec un prix unitaire par défaut (HT)."""

    key: str
    label: str
    unit_price: float


@dataclass(slots=True)
class LineItem:
    """Ligne de document (produit/service) avec quantité et remise facultative."""

    item_key: str
    description: str
    quantity: float
    unit_price: float
    discount_pct: float = 0.0  # 0–100

    def total_ht(self) -> float:
        """Return the line total excluding tax, applying discount if any."""
        price = self.quantity * self.unit_price
        if self.discount_pct:
            price *= max(0.0, 1.0 - (self.discount_pct / 100.0))
        return round(price, 2)


@dataclass(slots=True)
class Document:
    """Document (devis ou facture)."""

    doc_type: DocumentType
    issuer: Company
    customer: Party
    lines: list[LineItem] = field(default_factory=list)
    number: str | None = None
    date_: date = field(default_factory=date.today)
    notes: str | None = None

    def subtotal_ht(self) -> float:
        """Somme HT des lignes du document."""
        return round(sum(li.total_ht() for li in self.lines), 2)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the document."""
        return {
            'type': self.doc_type.value,
            'number': self.number,
            'date': self.date_.isoformat(),
            'issuer': self.issuer.__dict__,
            'customer': self.customer.__dict__,
            'lines': [
                {
                    'item_key': li.item_key,
                    'description': li.description,
                    'quantity': li.quantity,
                    'unit_price': li.unit_price,
                    'discount_pct': li.discount_pct,
                    'total_ht': li.total_ht(),
                }
                for li in self.lines
            ],
            'subtotal_ht': self.subtotal_ht(),
        }


if TYPE_CHECKING:
    from collections.abc import Iterable


def with_lines(doc: Document, lines: Iterable[LineItem]) -> Document:
    """Return the document after extending it with given lines."""
    doc.lines.extend(lines)
    return doc
