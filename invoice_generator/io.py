"""I/O helpers (JSON import) for documents.

This module keeps parsing logic out of the controller/view.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from .model import LineItem

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # import pour annotations uniquement
    from pathlib import Path


def parse_quote_json(path: Path) -> tuple[str, list[LineItem]]:
    """Parse a quote JSON file produced by ``export_json``.

    Returns a tuple (customer_name, lines).
    Unknown/missing fields are handled gracefully with defaults.
    """
    import json

    with path.open('r', encoding='utf-8') as f:
        data: dict[str, Any] = json.load(f)

    customer_name = ''
    if isinstance(data.get('customer'), dict):
        customer_name = str(data['customer'].get('name') or '')

    result: list[LineItem] = []
    for obj in data.get('lines', []) or []:
        # Validate structure first: must be a dict with required keys
        if not isinstance(obj, dict):
            logger.info('Ignoring non-dict line: %s', obj)
            continue
        required_keys = ('item_key', 'description', 'quantity', 'unit_price')
        if not all(k in obj for k in required_keys):
            logger.info('Ignoring malformed line (missing keys): %s', obj)
            continue
        try:
            key = str(obj.get('item_key') or '')
            desc = str(obj.get('description') or '')
            qty = float(obj.get('quantity') or 0.0)
            unit = float(obj.get('unit_price') or 0.0)
            disc = float(obj.get('discount_pct') or 0.0)
        except Exception:  # noqa: BLE001 - best-effort parsing with logging
            logger.exception('Malformed line in JSON: %s', obj)
            continue
        result.append(
            LineItem(
                item_key=key,
                description=desc,
                quantity=qty,
                unit_price=unit,
                discount_pct=disc,
            )
        )

    return customer_name, result
