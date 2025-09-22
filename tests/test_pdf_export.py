from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from invoice_generator.backend import export_pdf
from invoice_generator.model import Company
from invoice_generator.model import Document
from invoice_generator.model import DocumentType
from invoice_generator.model import LineItem
from invoice_generator.model import Party

if TYPE_CHECKING:  # noqa: TCH001 - typing only
    from pathlib import Path


@pytest.mark.parametrize(
    'doc_type',
    [DocumentType.QUOTE, DocumentType.INVOICE],
)
def test_export_pdf_produces_non_empty_file(tmp_path: Path, doc_type: DocumentType) -> None:
    issuer = Company(name='Ma Société')
    customer = Party(name='Client SA')
    lines = [
        LineItem(
            item_key='svc',
            description='Service',
            quantity=2,
            unit_price=100.0,
            discount_pct=10.0,
        ),
        LineItem(item_key='prod', description='Produit', quantity=1, unit_price=50.0),
    ]
    doc = Document(
        doc_type=doc_type,
        issuer=issuer,
        customer=customer,
        lines=lines,
        number='TST-0001',
    )

    out = tmp_path / f'{doc_type.value}.pdf'
    export_pdf(doc, out)

    assert out.exists(), "Le fichier PDF n'a pas été créé"
    size = out.stat().st_size
    # bornes faibles, juste pour vérifier qu'il n'est pas vide
    assert size > 200, f'PDF trop petit ({size}o) — export possiblement défaillant'
