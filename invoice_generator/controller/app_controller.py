"""Contrôleur principal reliant la vue, la config et le backend."""

from __future__ import annotations

from pathlib import Path

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

    def list_config_items(self) -> list[tuple[str, str, float]]:
        """Retourne les items (key, label, unit_price)."""
        items = self.config.list_items()
        return [(it['key'], it['label'], float(it['unit_price'])) for it in items]

    def upsert_item(self, key: str, label: str, unit_price: float) -> None:
        """Créer ou mettre à jour un item de la configuration."""
        self.config.upsert_item(key=key, label=label, unit_price=unit_price)

    def generate_document(
        self,
        doc_type: DocumentType,
        customer_name: str,
        lines: list[LineItem],
        number: str | None = None,
        notes: str | None = None,
        out_dir: Path | None = None,
    ) -> tuple[Path, Path]:
        """Génère le JSON et le PDF et retourne leurs chemins."""
        cfg_company = self.config.get_company()
        issuer = Company(
            name=cfg_company.get('name', 'Ma Société'),
            logo_path=cfg_company.get('logo_path'),
            logo_max_width=cfg_company.get('logo_max_width'),
        )
        customer = Party(name=customer_name)
        doc = Document(
            doc_type=doc_type,
            issuer=issuer,
            customer=customer,
            lines=lines,
            number=number,
            notes=notes,
        )

        out_dir = out_dir or (Path.home() / 'Documents' / 'Invoices')
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f'{doc_type.value}-{number or "draft"}'
        json_path = out_dir / f'{stem}.json'
        pdf_path = out_dir / f'{stem}.pdf'
        export_json(doc, json_path)
        export_pdf(doc, pdf_path)
        return json_path, pdf_path

    # Import/Export helpers
    def load_quote_from_json(self, path: Path) -> tuple[str, list[LineItem]]:
        """Charger un devis JSON (retourne client + lignes prêtes à injecter dans la vue)."""
        return parse_quote_json(path)
