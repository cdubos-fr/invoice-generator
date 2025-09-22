"""Backend de génération de documents (JSON et PDF)."""

from __future__ import annotations

import contextlib
import json
import textwrap
from typing import TYPE_CHECKING

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

if TYPE_CHECKING:  # imports uniquement pour les annotations
    from pathlib import Path

    from .model import Document


def _draw_header(
    c: canvas.Canvas,
    doc: Document,
    left: float,
    right: float,
    y_start: float,
    width: float,
    logo_max_width: float | None,
) -> float:
    """Dessine l'entête du document et retourne la nouvelle coordonnée Y.

    Affiche éventuellement un logo si ``doc.issuer.logo_path`` est défini.
    """
    y_loc = y_start
    c.setFont('Helvetica-Bold', 14)
    c.drawString(left, y_loc, f'{doc.doc_type.value.upper()} {doc.number or ""}')
    y_loc -= 20
    c.setFont('Helvetica', 10)
    c.drawString(left, y_loc, f'Date: {doc.date_.isoformat()}')
    y_loc -= 18
    if doc.issuer.logo_path:
        # Tente d'afficher le logo; ignore silencieusement en cas d'erreur
        with contextlib.suppress(Exception):
            c.drawImage(
                str(doc.issuer.logo_path),
                right - ((logo_max_width or 60.0) + 20),
                y_start - 10,
                width=(logo_max_width or 60.0),
                preserveAspectRatio=True,
                mask='auto',
            )
    c.drawString(left, y_loc, f'Emetteur: {doc.issuer.name}')
    y_loc -= 15
    c.drawString(left, y_loc, f'Client: {doc.customer.name}')
    y_loc -= 20
    return y_loc


def _draw_table_header(c: canvas.Canvas, left: float, right: float, y: float) -> float:
    c.setFont('Helvetica-Bold', 10)
    c.drawString(left, y, 'Description')
    c.drawString(300, y, 'Qté')
    c.drawString(340, y, 'PU')
    c.drawString(400, y, '% Rem.')
    c.drawString(460, y, 'Total HT')
    y -= 12
    c.line(left, y, right, y)
    y -= 8
    c.setFont('Helvetica', 10)
    return y


def _draw_footer(c: canvas.Canvas, page_num: int, width: float, bottom_margin: float) -> None:
    c.setFont('Helvetica-Oblique', 9)
    c.drawCentredString(width / 2, bottom_margin - 20, f'Page {page_num}')


def export_json(doc: Document, path: Path) -> None:
    """Export the document to JSON (UTF-8, indented)."""
    data = doc.to_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_pdf(doc: Document, path: Path) -> None:
    """Export un PDF avec entête, tableau paginé, notes et pied de page."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4

    left = 50
    right = width - 50
    top_margin = 50
    bottom_margin = 40

    page_num = 1

    # Début première page
    y = height - top_margin
    logo_max_width = doc.issuer.logo_max_width
    y = _draw_header(c, doc, left, right, y, width, logo_max_width)
    y = _draw_table_header(c, left, right, y)

    # Lignes
    for line in doc.lines:
        # Saut de page si on approche du bas
        if y < bottom_margin + 40:  # laisser de la place pour le footer
            _draw_footer(c, page_num, width, bottom_margin)
            c.showPage()
            page_num += 1
            y = height - top_margin
            y = _draw_header(c, doc, left, right, y, width, logo_max_width)
            y = _draw_table_header(c, left, right, y)
        c.drawString(left, y, line.description)
        c.drawRightString(330, y, f'{line.quantity:g}')
        c.drawRightString(390, y, f'{line.unit_price:.2f}')
        c.drawRightString(450, y, f'{line.discount_pct:.0f}')
        c.drawRightString(right, y, f'{line.total_ht():.2f}')
        y -= 14

    # Ligne de séparation et sous-total
    y -= 6
    c.line(left, y, right, y)
    y -= 18
    c.setFont('Helvetica-Bold', 11)
    c.drawRightString(right, y, f'Sous-total HT: {doc.subtotal_ht():.2f} €')
    y -= 16

    # Notes optionnelles
    if doc.notes:
        c.setFont('Helvetica-Bold', 10)
        c.drawString(left, y, 'Notes:')
        y -= 12
        c.setFont('Helvetica', 10)
        max_chars = 100
        for paragraph in str(doc.notes).splitlines() or ['']:
            text = textwrap.fill(paragraph, max_chars)
            for ln in text.splitlines():
                if y < bottom_margin + 20:
                    _draw_footer(c, page_num, width, bottom_margin)
                    c.showPage()
                    page_num += 1
                    y = height - top_margin
                    y = _draw_header(c, doc, left, right, y, width, logo_max_width)
                c.drawString(left, y, ln)
                y -= 12

    # Pied de page final et sauvegarde
    _draw_footer(c, page_num, width, bottom_margin)
    c.save()
