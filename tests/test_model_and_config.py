from __future__ import annotations

from pathlib import Path  # noqa: TCH003

from invoice_generator.config import DEFAULT_CONFIG
from invoice_generator.config import ConfigManager
from invoice_generator.model import Company
from invoice_generator.model import Document
from invoice_generator.model import DocumentType
from invoice_generator.model import LineItem
from invoice_generator.model import Party


def test_line_total_with_discount() -> None:
    li = LineItem(
        item_key='service', description='Consulting', quantity=10, unit_price=100.0, discount_pct=10
    )
    assert li.total_ht() == 900.0


def test_document_subtotal() -> None:
    doc = Document(
        doc_type=DocumentType.QUOTE,
        issuer=Company(name='ACME'),
        customer=Party(name='Client'),
        lines=[
            LineItem(item_key='a', description='A', quantity=1, unit_price=100.0),
            LineItem(item_key='b', description='B', quantity=2, unit_price=50.0, discount_pct=50),
        ],
    )
    # 100 + 2*50*0.5 = 100 + 50 = 150
    assert doc.subtotal_ht() == 150.0


def test_config_manager_roundtrip(tmp_path: Path) -> None:
    cfg = ConfigManager(path=tmp_path / 'config.json')
    data = cfg.load()
    assert data['company']['name'] == DEFAULT_CONFIG['company']['name']
    cfg.set_company_name('New Co')
    assert cfg.get_company()['name'] == 'New Co'
    # Logo roundtrip
    assert cfg.get_company().get('logo_path') is None
    cfg.set_company_logo_path(str(tmp_path / 'logo.png'))
    assert cfg.get_company().get('logo_path') == str(tmp_path / 'logo.png')
    cfg.upsert_item('x', 'X', 12.5)
    items = cfg.list_items()
    assert any(it['key'] == 'x' and it['unit_price'] == 12.5 for it in items)
