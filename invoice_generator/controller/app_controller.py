"""Contrôleur principal reliant la vue, la config et le backend."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # uniquement pour les annotations
    from datetime import date

from ..backend import export_json
from ..backend import export_pdf
from ..config import ConfigManager
from ..io import parse_quote_json
from ..model import Company
from ..model import Document
from ..model import DocumentType
from ..model import LineItem
from ..model import Party
from ..view.main_window import MainWindow


class AppController:
    """Contrôleur de l'application."""

    def __init__(self) -> None:
        """Initialize controller, configuration and view."""
        config_path = Path.home() / '.config' / 'invoice-generator' / 'config.json'
        self.config = ConfigManager(path=config_path)
        self.view = MainWindow(controller=self)

    def show(self) -> None:
        """Afficher la fenêtre principale."""
        self.view.show()

    # API appelée par la vue
    def get_company_name(self) -> str:
        """Retourner le nom de la société actuelle."""
        return self.config.get_company().get('name', '')

    def set_company_name(self, name: str) -> None:
        """Mettre à jour le nom de la société dans la configuration."""
        self.config.set_company_name(name)

    def get_company_logo_path(self) -> str | None:
        """Retourne le chemin du logo de la société (ou None)."""
        return self.config.get_company().get('logo_path')

    def set_company_logo_path(self, logo_path: str | None) -> None:
        """Met à jour le chemin du logo de la société."""
        self.config.set_company_logo_path(logo_path)

    def get_company_logo_max_width(self) -> float | None:
        """Retourne la largeur maximum du logo si configurée."""
        return self.config.get_company().get('logo_max_width')

    def set_company_logo_max_width(self, width: float | None) -> None:
        """Met à jour la largeur maximum du logo."""
        self.config.set_company_logo_max_width(width)

    def get_company_logo_max_height(self) -> float | None:
        """Retourne la hauteur maximum du logo si configurée."""
        return self.config.get_company().get('logo_max_height')

    def set_company_logo_max_height(self, height: float | None) -> None:
        """Met à jour la hauteur maximum du logo."""
        self.config.set_company_logo_max_height(height)

    def get_company_logo_margin_right(self) -> float | None:
        """Retourne la marge droite du logo si configurée."""
        return self.config.get_company().get('logo_margin_right')

    def set_company_logo_margin_right(self, margin: float | None) -> None:
        """Met à jour la marge droite du logo."""
        self.config.set_company_logo_margin_right(margin)

    # Coordonnées société
    def get_company_address(self) -> str | None:
        """Retourne l'adresse postale de la société si définie."""
        return self.config.get_company().get('address')

    def get_company_email(self) -> str | None:
        """Retourne l'email de la société si défini."""
        return self.config.get_company().get('email')

    def get_company_phone(self) -> str | None:
        """Retourne le téléphone de la société si défini."""
        return self.config.get_company().get('phone')

    def get_company_siret(self) -> str | None:
        """Retourne le SIRET de la société si défini."""
        return self.config.get_company().get('siret')

    def set_company_address(self, address: str | None) -> None:
        """Met à jour l'adresse postale de la société."""
        self.config.set_company_address(address)

    def set_company_email(self, email: str | None) -> None:
        """Met à jour l'adresse e-mail de la société."""
        self.config.set_company_email(email)

    def set_company_phone(self, phone: str | None) -> None:
        """Met à jour le numéro de téléphone de la société."""
        self.config.set_company_phone(phone)

    def set_company_siret(self, siret: str | None) -> None:
        """Met à jour le SIRET de la société."""
        self.config.set_company_siret(siret)

    def list_config_items(self) -> list[tuple[str, str, float]]:
        """Retourne les items (key, label, unit_price)."""
        items = self.config.list_items()
        flat = [(it['key'], it['label'], float(it['unit_price'])) for it in items]
        return sorted(flat, key=lambda t: t[0])

    def upsert_item(self, key: str, label: str, unit_price: float) -> None:
        """Créer ou mettre à jour un item de la configuration."""
        self.config.upsert_item(key=key, label=label, unit_price=unit_price)

    def delete_item(self, key: str) -> None:
        """Supprimer un item de la configuration par sa clé."""
        self.config.delete_item(key)

    def generate_document(
        self,
        doc_type: DocumentType,
        customer_name: str,
        lines: list[LineItem],
        *,
        number: str | None = None,
        notes: str | None = None,
        subject: str | None = None,
        validity_end_date: date | None = None,
        customer_address: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        customer_siret: str | None = None,
        out_dir: Path | None = None,
    ) -> tuple[Path, Path]:
        """Génère le JSON et le PDF et retourne leurs chemins."""
        cfg_company = self.config.get_company()
        issuer = Company(
            name=cfg_company.get('name', 'Ma Société'),
            logo_path=cfg_company.get('logo_path'),
            logo_max_width=cfg_company.get('logo_max_width'),
            logo_max_height=cfg_company.get('logo_max_height'),
            logo_margin_right=cfg_company.get('logo_margin_right'),
            address=cfg_company.get('address'),
            email=cfg_company.get('email'),
            phone=cfg_company.get('phone'),
            siret=cfg_company.get('siret'),
        )
        customer = Party(
            name=customer_name,
            address=customer_address,
            email=customer_email,
            phone=customer_phone,
            siret=customer_siret,
        )
        doc = Document(
            doc_type=doc_type,
            issuer=issuer,
            customer=customer,
            lines=lines,
            number=number,
            notes=notes,
            subject=subject,
            validity_end_date=validity_end_date,
        )

        # Numérotation: D- pour devis, F- pour facture
        if doc.number is None:
            if doc_type == DocumentType.QUOTE:
                doc.number = self.config.next_number('quote', prefix='D-')
            else:
                doc.number = self.config.next_number('invoice', prefix='F-')

        out_dir = out_dir or (Path.home() / 'Documents' / 'Invoices')
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f'{doc_type.value}-{doc.number}'
        json_path = out_dir / f'{stem}.json'
        pdf_path = out_dir / f'{stem}.pdf'
        export_json(doc, json_path)
        export_pdf(doc, pdf_path)
        return json_path, pdf_path

    # Import/Export helpers
    def load_quote_from_json(self, path: Path) -> tuple[str, list[LineItem]]:
        """Charger un devis JSON (retourne client + lignes prêtes à injecter dans la vue)."""
        return parse_quote_json(path)
