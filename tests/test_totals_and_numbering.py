from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from invoice_generator.backend import export_pdf
from invoice_generator.config import ConfigManager
from invoice_generator.io import parse_quote_json
from invoice_generator.model import Company
from invoice_generator.model import Document
from invoice_generator.model import DocumentType
from invoice_generator.model import LineItem
from invoice_generator.model import Party

if TYPE_CHECKING:  # noqa: TCH001
    from pathlib import Path


def test_document_totals_and_to_dict() -> None:
    issuer = Company(name='Iss', email='i@example.com')
    customer = Party(name='Cli', email='c@example.com')
    lines = [
        LineItem(item_key='a', description='A', quantity=2, unit_price=100.0, tax_pct=20.0),
        LineItem(
            item_key='b',
            description='B',
            quantity=1,
            unit_price=50.0,
            discount_pct=50.0,
            tax_pct=5.0,
        ),
    ]
    doc = Document(
        doc_type=DocumentType.QUOTE,
        issuer=issuer,
        customer=customer,
        lines=lines,
        number='D-0001',
        subject='Prestation X',
        validity_end_date=date(2025, 12, 31),
        notes='Note 1\nNote 2',
    )
    # Subtotal: 2*100 + 1*50*0.5 = 200 + 25 = 225
    assert doc.subtotal_ht() == 225.0
    # TVA: 200*20% + 25*5% = 40 + 1.25 = 41.25
    assert round(doc.total_tva(), 2) == 41.25
    # Net: 225 + 41.25 = 266.25
    assert round(doc.net_to_pay(), 2) == 266.25
    data = doc.to_dict()
    assert data['subtotal_ht'] == 225.0
    assert data['total_tva'] == 41.25
    assert data['net_to_pay'] == 266.25
    assert data['subject'] == 'Prestation X'
    assert data['validity_end_date'] == '2025-12-31'


def test_config_next_number(tmp_path: Path) -> None:
    cfg = ConfigManager(path=tmp_path / 'cfg.json')
    n1 = cfg.next_number('quote', prefix='D-', width=4)
    n2 = cfg.next_number('quote', prefix='D-', width=4)
    m1 = cfg.next_number('invoice', prefix='F-', width=5)
    assert n1 == 'D-0001'
    assert n2 == 'D-0002'
    assert m1 == 'F-00001'


def test_io_parse_extended_fields(tmp_path: Path) -> None:
    import json

    data = {
        'customer': {'name': 'ACME'},
        'lines': [
            {
                'item_key': 'svc',
                'description': 'Service',
                'quantity': 3,
                'unit_price': 80.0,
                'discount_pct': 10.0,
                'unit': 'h',
                'tax_pct': 20.0,
            }
        ],
    }
    path = tmp_path / 'q.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    customer_name, lines = parse_quote_json(path)
    assert customer_name == 'ACME'
    assert len(lines) == 1
    li = lines[0]
    assert li.unit == 'h'
    assert li.tax_pct == 20.0


def test_export_pdf_rich_content_triggers_blocks(tmp_path: Path) -> None:
    # Créer suffisamment de lignes pour forcer un saut de page
    issuer = Company(
        name='My Co',
        address='1 rue de la Paix',
        email='me@co.example',
        phone='+33 1 23 45 67 89',
        siret='123 456 789 00010',
        logo_path=str(tmp_path / 'no-logo.png'),  # inexistant -> suppress(Exception) couvert
        logo_max_width=80.0,
        logo_max_height=40.0,
        logo_margin_right=10.0,
    )
    customer = Party(name='Foo Inc', address='Somewhere')
    # ~40 lignes de 14 px -> > 560 px, assez pour paginer
    lines = [
        LineItem(item_key=f'k{i}', description=f'Ligne {i}', quantity=1, unit_price=1.0)
        for i in range(40)
    ]
    doc = Document(
        doc_type=DocumentType.QUOTE,
        issuer=issuer,
        customer=customer,
        lines=lines,
        number='D-4242',
        subject='Sujet de test',
        validity_end_date=date(2025, 1, 31),
        notes='Ligne A\nLigne B',
    )
    out = tmp_path / 'rich.pdf'
    export_pdf(doc, out)
    assert out.exists()
    assert out.stat().st_size > 200
