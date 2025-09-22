"""Backend de génération de documents (JSON et PDF)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

if TYPE_CHECKING:  # imports uniquement pour les annotations
    from pathlib import Path

    from .model import Document


def export_json(doc: Document, path: Path) -> None:
    """Export the document to JSON (UTF-8, indented)."""
    data = doc.to_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_pdf(doc: Document, path: Path) -> None:
    """Export a minimal PDF listing header and lines.

    This initial version is intentionally simple and will be enhanced later.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont('Helvetica-Bold', 14)
    c.drawString(50, y, f'{doc.doc_type.value.upper()} {doc.number or ""}')
    y -= 20
    c.setFont('Helvetica', 10)
    c.drawString(50, y, f'Date: {doc.date_.isoformat()}')
    y -= 20
    c.drawString(50, y, f'Emetteur: {doc.issuer.name}')
    y -= 15
    c.drawString(50, y, f'Client: {doc.customer.name}')
    y -= 30

    c.setFont('Helvetica-Bold', 10)
    c.drawString(50, y, 'Description')
    c.drawString(300, y, 'Qté')
    c.drawString(340, y, 'PU')
    c.drawString(400, y, '% Rem.')
    c.drawString(460, y, 'Total HT')
    y -= 15
    c.line(50, y, width - 50, y)
    y -= 10

    c.setFont('Helvetica', 10)
    for line in doc.lines:
        if y < 80:
            c.showPage()
            y = height - 80
            c.setFont('Helvetica', 10)
        c.drawString(50, y, line.description)
        c.drawRightString(330, y, f'{line.quantity:g}')
        c.drawRightString(390, y, f'{line.unit_price:.2f}')
        c.drawRightString(450, y, f'{line.discount_pct:.0f}')
        c.drawRightString(width - 50, y, f'{line.total_ht():.2f}')
        y -= 15

    y -= 10
    c.line(50, y, width - 50, y)
    y -= 20
    c.setFont('Helvetica-Bold', 11)
    c.drawRightString(width - 50, y, f'Sous-total HT: {doc.subtotal_ht():.2f} €')

    c.showPage()
    c.save()
