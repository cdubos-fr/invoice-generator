from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # noqa: TCH001 - used for typing only
    from pathlib import Path

from invoice_generator.io import parse_quote_json
from invoice_generator.model import LineItem


def write_json(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / 'quote.json'
    p.write_text(json.dumps(data), encoding='utf-8')
    return p


def test_parse_quote_happy_path(tmp_path: Path) -> None:
    data = {
        'customer': {'name': 'ACME'},
        'lines': [
            {
                'item_key': 'srv',
                'description': 'Service',
                'quantity': 2,
                'unit_price': 100.0,
                'discount_pct': 10.0,
            }
        ],
    }
    path = write_json(tmp_path, data)
    customer, lines = parse_quote_json(path)
    assert customer == 'ACME'
    assert len(lines) == 1
    li = lines[0]
    assert isinstance(li, LineItem)
    assert li.item_key == 'srv'
    assert li.description == 'Service'
    assert li.quantity == 2
    assert li.unit_price == 100.0
    assert li.discount_pct == 10.0


def test_parse_quote_missing_discount_defaults_to_zero(tmp_path: Path) -> None:
    data = {
        'customer': {'name': 'Foo'},
        'lines': [
            {
                'item_key': 'prod',
                'description': 'Produit',
                'quantity': 1,
                'unit_price': 9.99,
            }
        ],
    }
    path = write_json(tmp_path, data)
    customer, lines = parse_quote_json(path)
    assert customer == 'Foo'
    assert len(lines) == 1
    assert lines[0].discount_pct == 0.0


def test_parse_quote_malformed_line_is_ignored(tmp_path: Path) -> None:
    data = {
        'customer': {'name': 'Bar'},
        'lines': [
            {'item_key': 'ok', 'description': 'OK', 'quantity': 1, 'unit_price': 5.0},
            {'bad': 'line'},  # should be ignored
        ],
    }
    path = write_json(tmp_path, data)
    customer, lines = parse_quote_json(path)
    assert customer == 'Bar'
    assert len(lines) == 1
    assert lines[0].item_key == 'ok'
