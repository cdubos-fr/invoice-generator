"""Modèles de domaine pour devis et factures.

Fournit des dataclasses modernes décrivant les entités manipulées par le backend (PDF/JSON)
et le frontend (UI PyQt6). Ces modèles sont agnostiques de l'interface.
"""

from __future__ import annotations

from dataclasses import asdict
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
    logo_max_width: float | None = None
    logo_max_height: float | None = None
    logo_margin_right: float | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    siret: str | None = None


@dataclass(slots=True)
class Party:
    """Tiers (client/destinataire) du document."""

    name: str
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    siret: str | None = None


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
    unit: str = ''
    tax_pct: float = 0.0  # 0–100

    def total_ht(self) -> float:
        """Return the line total excluding tax, applying discount if any."""
        price = self.quantity * self.unit_price
        if self.discount_pct:
            price *= max(0.0, 1.0 - (self.discount_pct / 100.0))
        return round(price, 2)


def _sum(values: list[float]) -> float:
    return round(sum(values), 2)


# (Plus d’attribution dynamique de méthodes — méthodes définies dans la classe)


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
    subject: str | None = None
    validity_end_date: date | None = None

    def subtotal_ht(self) -> float:
        """Somme HT des lignes du document."""
        return round(sum(li.total_ht() for li in self.lines), 2)

    def total_tva(self) -> float:
        """Total de TVA calculé à partir des lignes (en fonction de tax_pct)."""
        return _sum([li.total_ht() * max(0.0, li.tax_pct) / 100.0 for li in self.lines])

    def net_to_pay(self) -> float:
        """Montant TTC à payer (HT + TVA)."""
        return round(self.subtotal_ht() + self.total_tva(), 2)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the document."""
        return {
            'type': self.doc_type.value,
            'number': self.number,
            'date': self.date_.isoformat(),
            'issuer': asdict(self.issuer),
            'customer': asdict(self.customer),
            'lines': [
                {
                    'item_key': li.item_key,
                    'description': li.description,
                    'quantity': li.quantity,
                    'unit_price': li.unit_price,
                    'discount_pct': li.discount_pct,
                    'unit': li.unit,
                    'tax_pct': li.tax_pct,
                    'total_ht': li.total_ht(),
                }
                for li in self.lines
            ],
            'subtotal_ht': self.subtotal_ht(),
            'total_tva': self.total_tva(),
            'net_to_pay': self.net_to_pay(),
            'subject': self.subject,
            'validity_end_date': self.validity_end_date.isoformat()
            if self.validity_end_date
            else None,
        }


if TYPE_CHECKING:
    from collections.abc import Iterable


def with_lines(doc: Document, lines: Iterable[LineItem]) -> Document:
    """Return the document after extending it with given lines."""
    doc.lines.extend(lines)
    return doc
