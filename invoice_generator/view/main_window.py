"""Vue PyQt6: fenêtre principale avec trois onglets.

Cette vue reste volontairement minimale à ce stade et délègue au contrôleur.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QGroupBox
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtWidgets import QTableWidget
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtWidgets import QWidget

from ..model import DocumentType
from ..model import LineItem


class _ControllerProto(Protocol):
    def get_company_name(self) -> str: ...
    def set_company_name(self, name: str) -> None: ...
    def list_config_items(self) -> list[tuple[str, str, float]]: ...
    def upsert_item(self, key: str, label: str, unit_price: float) -> None: ...
    def generate_document(
        self, doc_type: DocumentType, customer_name: str, lines: list[LineItem]
    ) -> tuple[object, object]: ...


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    # Helpers
    def _add_line(self, table: QTableWidget) -> None:
        row = table.rowCount()
        table.insertRow(row)
        # Item dropdown
        combo = QComboBox()
        for key, label, price in self._controller.list_config_items():
            combo.addItem(f'{label} ({price:.2f}€)', userData=(key, price))
        table.setCellWidget(row, 0, combo)

        # Description
        table.setItem(row, 1, QTableWidgetItem(''))

        # Quantity
        qty = QSpinBox()
        qty.setRange(1, 1_000_000)
        qty.setValue(1)
        table.setCellWidget(row, 2, qty)

        # Unit price (non éditable, issu de l'item)
        price_item = QTableWidgetItem('0.00')
        price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 3, price_item)

        # Discount
        disc = QDoubleSpinBox()
        disc.setRange(0.0, 100.0)
        disc.setDecimals(0)
        table.setCellWidget(row, 4, disc)

        def update_price() -> None:
            _key, p = combo.currentData()
            table.item(row, 3).setText(f'{float(p):.2f}')

        combo.currentIndexChanged.connect(update_price)
        update_price()

    def _collect_lines(self, table: QTableWidget) -> list[LineItem]:
        lines: list[LineItem] = []
        for row in range(table.rowCount()):
            combo = table.cellWidget(row, 0)
            if not isinstance(combo, QComboBox):
                continue
            key, price = combo.currentData()
            desc = table.item(row, 1).text() if table.item(row, 1) else ''
            qty = table.cellWidget(row, 2)
            if not isinstance(qty, QSpinBox):
                continue
            qty_v = float(qty.value())
            disc = table.cellWidget(row, 4)
            if not isinstance(disc, QDoubleSpinBox):
                continue
            disc_v = float(disc.value())
            lines.append(
                LineItem(
                    item_key=key,
                    description=desc,
                    quantity=qty_v,
                    unit_price=float(price),
                    discount_pct=disc_v,
                )
            )
        return lines

    # Slots
    def _on_generate_quote(self) -> None:
        lines = self._collect_lines(self.quote_table)
        self._controller.generate_document(DocumentType.QUOTE, self.quote_customer.text(), lines)

    def _setup_quote_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QHBoxLayout()
        form.addWidget(QLabel('Client:'))
        self.quote_customer = QLineEdit()
        form.addWidget(self.quote_customer)
        layout.addLayout(form)

        self.quote_table = QTableWidget(0, 5)
        self.quote_table.setHorizontalHeaderLabels(['Item', 'Description', 'Qté', 'PU', '% Rem.'])
        layout.addWidget(self.quote_table)

        btns = QHBoxLayout()
        add_btn = QPushButton('Ajouter ligne')
        add_btn.clicked.connect(lambda: self._add_line(self.quote_table))
        gen_btn = QPushButton('Générer devis')
        gen_btn.clicked.connect(self._on_generate_quote)
        btns.addWidget(add_btn)
        btns.addStretch(1)
        btns.addWidget(gen_btn)
        layout.addLayout(btns)

        self.tabs.addTab(tab, 'Devis')

    def _on_generate_invoice(self) -> None:
        lines = self._collect_lines(self.invoice_table)
        self._controller.generate_document(
            DocumentType.INVOICE, self.invoice_customer.text(), lines
        )

    def _on_import_quote(self) -> None:
        # Boîte de dialogue pour choisir un devis JSON exporté
        path, _ = QFileDialog.getOpenFileName(self, 'Importer un devis (JSON)', '', 'JSON (*.json)')
        if not path:
            return
        customer, lines = self._controller.load_quote_from_json(Path(path))

        # Renseigner le client et les lignes dans l’onglet facture
        self.invoice_customer.setText(customer)
        self.invoice_table.setRowCount(0)
        for li in lines:
            self._add_line(self.invoice_table)
            row = self.invoice_table.rowCount() - 1
            combo = self.invoice_table.cellWidget(row, 0)
            if isinstance(combo, QComboBox):
                # Tenter de sélectionner l'item correspondant à la clé
                for i in range(combo.count()):
                    data = combo.itemData(i)
                    if isinstance(data, tuple) and data[0] == li.item_key:
                        combo.setCurrentIndex(i)
                        break
            # Description
            self.invoice_table.item(row, 1).setText(li.description)
            # Quantité
            qty = self.invoice_table.cellWidget(row, 2)
            if isinstance(qty, QSpinBox):
                qty.setValue(int(li.quantity))
            # Remise
            disc = self.invoice_table.cellWidget(row, 4)
            if isinstance(disc, QDoubleSpinBox):
                disc.setValue(float(li.discount_pct))

    def _setup_invoice_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QHBoxLayout()
        form.addWidget(QLabel('Client:'))
        self.invoice_customer = QLineEdit()
        form.addWidget(self.invoice_customer)

        load_quote_btn = QPushButton('Importer depuis devis JSON')
        load_quote_btn.clicked.connect(self._on_import_quote)
        form.addWidget(load_quote_btn)
        layout.addLayout(form)

        self.invoice_table = QTableWidget(0, 5)
        self.invoice_table.setHorizontalHeaderLabels(['Item', 'Description', 'Qté', 'PU', '% Rem.'])
        layout.addWidget(self.invoice_table)

        btns = QHBoxLayout()
        add_btn = QPushButton('Ajouter ligne')
        add_btn.clicked.connect(lambda: self._add_line(self.invoice_table))
        gen_btn = QPushButton('Générer facture')
        gen_btn.clicked.connect(self._on_generate_invoice)
        btns.addWidget(add_btn)
        btns.addStretch(1)
        btns.addWidget(gen_btn)
        layout.addLayout(btns)

        self.tabs.addTab(tab, 'Facture')

    def _refresh_items_grid(self, grid: QGridLayout) -> None:
        items = self._controller.list_config_items()
        for row, (key, label, price) in enumerate(items, start=1):
            key_edit = QLineEdit(key)
            label_edit = QLineEdit(label)
            price_edit = QDoubleSpinBox()
            price_edit.setRange(0.0, 10_000_000.0)
            price_edit.setDecimals(2)
            price_edit.setValue(price)

            def on_change(
                key_edit: QLineEdit = key_edit,
                label_edit: QLineEdit = label_edit,
                price_edit: QDoubleSpinBox = price_edit,
            ) -> None:
                self._controller.upsert_item(
                    key_edit.text(), label_edit.text(), float(price_edit.value())
                )

            key_edit.editingFinished.connect(on_change)
            label_edit.editingFinished.connect(on_change)
            price_edit.editingFinished.connect(on_change)

            grid.addWidget(key_edit, row, 0)
            grid.addWidget(label_edit, row, 1)
            grid.addWidget(price_edit, row, 2)

    def _setup_config_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        company_box = QGroupBox('Société émettrice')
        g = QGridLayout(company_box)
        g.addWidget(QLabel('Nom:'), 0, 0)
        self.company_name = QLineEdit(self._controller.get_company_name())
        self.company_name.editingFinished.connect(
            lambda: self._controller.set_company_name(self.company_name.text())
        )
        g.addWidget(self.company_name, 0, 1)
        layout.addWidget(company_box)

        items_box = QGroupBox('Produits/Services')
        gi = QGridLayout(items_box)
        gi.addWidget(QLabel('Clé'), 0, 0)
        gi.addWidget(QLabel('Libellé'), 0, 1)
        gi.addWidget(QLabel('Prix unitaire'), 0, 2)

        self._refresh_items_grid(gi)
        layout.addWidget(items_box)

        self.tabs.addTab(tab, 'Configuration')

    def __init__(self, controller: _ControllerProto) -> None:
        """Initialize the main window and its tabs."""
        super().__init__()
        self._controller = controller
        self.setWindowTitle('Invoice Generator')
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._setup_quote_tab()
        self._setup_invoice_tab()
        self._setup_config_tab()
