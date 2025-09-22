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
    logo_max_height: float | None,
    logo_margin_right: float | None,
) -> float:
    """Dessine l'entête (titre + date + logo) et retourne la nouvelle coordonnée Y."""
    y_loc = y_start
    c.setFont('Helvetica-Bold', 14)
    title = 'DEVIS' if str(doc.doc_type) == 'DocumentType.QUOTE' else 'FACTURE'
    c.drawString(left, y_loc, f'{title} {doc.number or ""}')
    y_loc -= 20
    c.setFont('Helvetica', 10)
    c.drawString(left, y_loc, f'Date: {doc.date_.isoformat()}')
    y_loc -= 18
    if doc.issuer.logo_path:
        # Tente d'afficher le logo; ignore silencieusement en cas d'erreur
        with contextlib.suppress(Exception):
            w = logo_max_width or 60.0
            h = logo_max_height or w
            mr = logo_margin_right or 20.0
            c.drawImage(
                str(doc.issuer.logo_path),
                right - (w + mr),
                y_start - 10,
                width=w,
                height=h,
                preserveAspectRatio=True,
                mask='auto',
            )
    return y_loc


def _draw_parties_frames(
    c: canvas.Canvas, doc: Document, left: float, right: float, y: float
) -> float:
    """Dessine les cadres Émetteur/Client côte à côte, retourne le Y suivant."""
    c.setFont('Helvetica-Bold', 10)
    mid = (left + right) / 2
    # Cadre Émetteur (gauche)
    c.drawString(left, y, 'Émetteur')
    y -= 12
    c.setFont('Helvetica', 9)
    issuer_lines = [
        doc.issuer.name,
        doc.issuer.address or '',
        f'Email: {doc.issuer.email}' if doc.issuer.email else '',
        f'Téléphone: {doc.issuer.phone}' if doc.issuer.phone else '',
        f'SIRET: {doc.issuer.siret}' if doc.issuer.siret else '',
    ]
    for ln in issuer_lines:
        if ln:
            c.drawString(left, y, ln)
            y -= 12
    # Relever y pour la zone client (commence en haut du bloc émetteur)
    y_client = y + 12 * (len([ln for ln in issuer_lines if ln]) + 1)
    c.setFont('Helvetica-Bold', 10)
    c.drawString(mid + 10, y_client, 'Client')
    y_client -= 12
    c.setFont('Helvetica', 9)
    client_lines = [
        doc.customer.name,
        doc.customer.address or '',
        f'Email: {doc.customer.email}' if doc.customer.email else '',
        f'Téléphone: {doc.customer.phone}' if doc.customer.phone else '',
        f'SIRET: {doc.customer.siret}' if doc.customer.siret else '',
    ]
    for ln in client_lines:
        if ln:
            c.drawString(mid + 10, y_client, ln)
            y_client -= 12
    # Retourner le Y minimum des deux colonnes - petit espace
    return min(y, y_client) - 10


def _draw_realization_block(
    c: canvas.Canvas, doc: Document, left: float, right: float, y: float
) -> float:
    """Bloc Sujet/Validité au-dessus du tableau (pour devis notamment)."""
    if not doc.subject and not doc.validity_end_date:
        return y
    c.setFont('Helvetica-Bold', 10)
    c.drawString(left, y, 'Réalisation')
    y -= 12
    c.setFont('Helvetica', 9)
    if doc.subject:
        c.drawString(left, y, f'Sujet: {doc.subject}')
        y -= 12
    if doc.validity_end_date:
        c.drawString(left, y, f'Validité du devis: {doc.validity_end_date.isoformat()}')
        y -= 12
    y -= 6
    c.line(left, y, right, y)
    y -= 8
    return y


def _draw_table_header(c: canvas.Canvas, left: float, right: float, y: float) -> float:
    c.setFont('Helvetica-Bold', 10)
    c.drawString(left, y, 'Description')
    c.drawString(300, y, 'Unité')
    c.drawString(350, y, 'Qté')
    c.drawString(390, y, 'PU')
    c.drawString(440, y, 'TVA %')
    c.drawString(490, y, '% Rem.')
    c.drawString(540, y, 'Total HT')
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
    logo_max_height = doc.issuer.logo_max_height
    logo_margin_right = doc.issuer.logo_margin_right
    y = _draw_header(
        c,
        doc,
        left,
        right,
        y,
        width,
        logo_max_width,
        logo_max_height,
        logo_margin_right,
    )
    # Cadres émetteur/client
    y = _draw_parties_frames(c, doc, left, right, y)
    # Bloc réalisation (sujet/validité)
    y = _draw_realization_block(c, doc, left, right, y)
    y = _draw_table_header(c, left, right, y)

    # Lignes
    for line in doc.lines:
        # Saut de page si on approche du bas
        if y < bottom_margin + 60:  # laisser de la place pour le footer
            _draw_footer(c, page_num, width, bottom_margin)
            c.showPage()
            page_num += 1
            y = height - top_margin
            y = _draw_header(
                c,
                doc,
                left,
                right,
                y,
                width,
                logo_max_width,
                logo_max_height,
                logo_margin_right,
            )
            y = _draw_table_header(c, left, right, y)
        # Fallback: si description vide, utiliser la clé de l'item
        desc = (line.description or '').strip() or line.item_key
        c.drawString(left, y, desc)
        c.drawString(300, y, (line.unit or ''))
        c.drawRightString(380, y, f'{line.quantity:g}')
        c.drawRightString(430, y, f'{line.unit_price:.2f}')
        c.drawRightString(490, y, f'{line.tax_pct:.0f}')
        c.drawRightString(540, y, f'{line.discount_pct:.0f}')
        c.drawRightString(right, y, f'{line.total_ht():.2f}')
        y -= 14

    # Ligne de séparation et sous-total
    y -= 6
    c.line(left, y, right, y)
    y -= 18
    c.setFont('Helvetica-Bold', 11)
    c.drawRightString(right, y, f'TOTAL HT: {doc.subtotal_ht():.2f} €')
    y -= 14
    c.setFont('Helvetica', 10)
    c.drawRightString(right, y, f'TOTAL TVA: {doc.total_tva():.2f} €')
    y -= 14
    c.setFont('Helvetica-Bold', 12)
    c.drawRightString(right, y, f'Net à payer: {doc.net_to_pay():.2f} €')
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
                    y = _draw_header(
                        c,
                        doc,
                        left,
                        right,
                        y,
                        width,
                        logo_max_width,
                        logo_max_height,
                        logo_margin_right,
                    )
                c.drawString(left, y, ln)
                y -= 12

    # Pied de page final et sauvegarde
    _draw_footer(c, page_num, width, bottom_margin)
    c.save()
