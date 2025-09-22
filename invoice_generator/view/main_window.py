"""Vue PyQt6: fenêtre principale avec trois onglets.

Cette vue reste volontairement minimale à ce stade et délègue au contrôleur.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Protocol

from PyQt6.QtCore import Qt
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtWidgets import QDoubleSpinBox
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtWidgets import QGridLayout
from PyQt6.QtWidgets import QGroupBox
from PyQt6.QtWidgets import QHBoxLayout
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtWidgets import QMessageBox
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
    def get_company_logo_path(self) -> str | None: ...
    def set_company_logo_path(self, logo_path: str | None) -> None: ...
    def get_company_address(self) -> str | None: ...
    def set_company_address(self, address: str | None) -> None: ...
    def get_company_email(self) -> str | None: ...
    def set_company_email(self, email: str | None) -> None: ...
    def get_company_phone(self) -> str | None: ...
    def set_company_phone(self, phone: str | None) -> None: ...
    def get_company_siret(self) -> str | None: ...
    def set_company_siret(self, siret: str | None) -> None: ...
    def list_config_items(self) -> list[tuple[str, str, float]]: ...
    def upsert_item(self, key: str, label: str, unit_price: float) -> None: ...
    def delete_item(self, key: str) -> None: ...
    def generate_document(
        self,
        doc_type: DocumentType,
        customer_name: str,
        lines: list[LineItem],
        *,
        subject: str | None = None,
        validity_end_date: date | None = None,
        customer_address: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        customer_siret: str | None = None,
    ) -> tuple[Path, Path]: ...
    def load_quote_from_json(self, path: Path) -> tuple[str, list[LineItem]]: ...
    def get_company_logo_max_width(self) -> float | None: ...
    def set_company_logo_max_width(self, width: float | None) -> None: ...
    def get_company_logo_max_height(self) -> float | None: ...
    def set_company_logo_max_height(self, height: float | None) -> None: ...
    def get_company_logo_margin_right(self) -> float | None: ...
    def set_company_logo_margin_right(self, margin: float | None) -> None: ...


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def _find_parent_table(self, obj: object) -> QTableWidget | None:
        # Monte la chaîne parentale jusqu'à trouver le QTableWidget
        try:
            from PyQt6.QtWidgets import QWidget as QWidgetCls
        except Exception:
            return None
        w = obj
        depth = 0
        # Par précaution, on limite la profondeur pour éviter toute boucle pathologique
        while isinstance(w, QWidgetCls) and depth < 32:
            if isinstance(w, QTableWidget):
                return w
            w = w.parentWidget()
            depth += 1
        return None

    def _recompute_row_totals(self, table: QTableWidget, row: int) -> None:
        # Garde-fous basiques
        if row < 0 or row >= table.rowCount():
            return
        # Bloquer les signaux du tableau pendant la mise à jour pour éviter toute ré-entrée
        table.blockSignals(True)
        try:
            combo = table.cellWidget(row, 0)
            price_value = 0.0
            if isinstance(combo, QComboBox):
                data = combo.currentData()
                if isinstance(data, tuple) and len(data) >= 2:
                    _, price_value = data
            # Mettre à jour PU
            item_price = table.item(row, 4)
            if isinstance(item_price, QTableWidgetItem):
                item_price.setText(f'{float(price_value):.2f}')
            # Calcul total HT
            qty_w = table.cellWidget(row, 3)
            disc_w = table.cellWidget(row, 6)
            qv = float(qty_w.value()) if isinstance(qty_w, QSpinBox) else 0.0
            dv = float(disc_w.value()) if isinstance(disc_w, QDoubleSpinBox) else 0.0
            line_total = qv * float(price_value)
            if dv:
                line_total *= max(0.0, 1.0 - dv / 100.0)
            item_total = table.item(row, 7)
            if isinstance(item_total, QTableWidgetItem):
                item_total.setText(f'{line_total:.2f}')
        finally:
            table.blockSignals(False)

    def _find_row_for_sender(self, table: QTableWidget, sender: object) -> int | None:
        """Retourne l'indice de ligne du widget `sender` en scannant des colonnes connues."""
        widget_cols = (0, 2, 3, 5, 6)
        for r in range(table.rowCount()):
            for c in widget_cols:
                w = table.cellWidget(r, c)
                if w is sender:
                    return r
        return None

    def _collect_lines(self, table: QTableWidget) -> list[LineItem]:
        lines: list[LineItem] = []
        for row in range(table.rowCount()):
            combo = table.cellWidget(row, 0)
            if not isinstance(combo, QComboBox):
                continue
            data = combo.currentData()
            if not (isinstance(data, tuple) and len(data) >= 2):
                # Ligne incomplète, on ignore
                continue
            key, price = data[0], data[1]
            cell = table.item(row, 1)
            desc = cell.text() if isinstance(cell, QTableWidgetItem) else ''
            unit = ''
            unit_w = table.cellWidget(row, 2)
            if isinstance(unit_w, QComboBox):
                unit = unit_w.currentText()
            qty = table.cellWidget(row, 3)
            if not isinstance(qty, QSpinBox):
                continue
            qty_v = float(qty.value())
            tax = table.cellWidget(row, 5)
            tax_v = float(tax.value()) if isinstance(tax, QDoubleSpinBox) else 0.0
            disc = table.cellWidget(row, 6)
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
                    unit=unit,
                    tax_pct=tax_v,
                )
            )
        return lines

    def _recompute_table_totals(self, table: QTableWidget) -> None:
        """Met à jour les labels des totaux pour le tableau fourni."""
        lines = self._collect_lines(table)
        total_ht = sum(li.total_ht() for li in lines)
        total_tva = sum(li.total_ht() * max(0.0, li.tax_pct) / 100.0 for li in lines)
        total_net = round(total_ht + total_tva, 2)

        if hasattr(self, 'quote_table') and table is self.quote_table:
            self.quote_total_ht_label.setText(f'Total HT: {total_ht:.2f} €')
            self.quote_total_tva_label.setText(f'Total TVA: {total_tva:.2f} €')
            self.quote_total_net_label.setText(f'Net à payer: {total_net:.2f} €')
        elif hasattr(self, 'invoice_table') and table is self.invoice_table:
            self.invoice_total_ht_label.setText(f'Total HT: {total_ht:.2f} €')
            self.invoice_total_tva_label.setText(f'Total TVA: {total_tva:.2f} €')
            self.invoice_total_net_label.setText(f'Net à payer: {total_net:.2f} €')

    def _on_row_widget_changed(self, *_args: object) -> None:
        sender = self.sender()
        if sender is None:
            return
        # Retrouver le QTableWidget parent sans capturer de référence dans une closure
        table = self._find_parent_table(sender)
        if table is None:
            return
        try:
            row = int(sender.property('row'))
        except Exception:
            row = -1
        if row < 0 or row >= table.rowCount():
            # Fallback: scanner pour retrouver la ligne correspondant au widget émetteur
            found = self._find_row_for_sender(table, sender)
            if found is None:
                return
            row = found
        self._recompute_row_totals(table, row)
        self._recompute_table_totals(table)

    # Helpers
    def _add_line(self, table: QTableWidget) -> None:
        row = table.rowCount()
        table.insertRow(row)
        # Item dropdown
        combo = QComboBox()
        for key, label, price in sorted(self._controller.list_config_items(), key=lambda t: t[0]):
            combo.addItem(f'{label} ({price:.2f}€)', userData=(key, price))
        table.setCellWidget(row, 0, combo)

        # Description
        desc_item = QTableWidgetItem('')
        table.setItem(row, 1, desc_item)

        # Unité (combo éditable)
        unit_combo = QComboBox()
        unit_combo.setEditable(True)
        unit_combo.addItems(['h', 'jour', 'pièce'])
        table.setCellWidget(row, 2, unit_combo)

        # Quantité
        qty = QSpinBox()
        qty.setRange(1, 1_000_000)
        qty.setValue(1)
        table.setCellWidget(row, 3, qty)

        # Prix unitaire (non éditable, issu de l'item)
        price_item = QTableWidgetItem('0.00')
        price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 4, price_item)

        # TVA %
        tax = QDoubleSpinBox()
        tax.setRange(0.0, 100.0)
        tax.setDecimals(0)
        tax.setValue(20.0)
        table.setCellWidget(row, 5, tax)

        # Remise %
        disc = QDoubleSpinBox()
        disc.setRange(0.0, 100.0)
        disc.setDecimals(0)
        table.setCellWidget(row, 6, disc)

        # Total HT (lecture seule)
        total_item = QTableWidgetItem('0.00')
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 7, total_item)

        # Stocker l'indice de ligne sur les widgets (éviter les closures fragiles)
        for w in (combo, unit_combo, qty, tax, disc):
            w.setProperty('row', row)

        # Connexions vers un slot d'instance
        combo.currentIndexChanged.connect(self._on_row_widget_changed)
        qty.valueChanged.connect(self._on_row_widget_changed)
        tax.valueChanged.connect(self._on_row_widget_changed)
        disc.valueChanged.connect(self._on_row_widget_changed)
        self._recompute_row_totals(table, row)

    def _show_generation_result(self, json_path: Path, pdf_path: Path) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle('Document généré')
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText('Fichiers générés:')
        msg.setInformativeText(f'- PDF: {pdf_path}\n- JSON: {json_path}')
        btn_open_pdf = msg.addButton('Ouvrir PDF', QMessageBox.ButtonRole.AcceptRole)
        btn_open_dir = msg.addButton('Ouvrir dossier', QMessageBox.ButtonRole.ActionRole)
        msg.addButton('Fermer', QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == btn_open_pdf:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))
        elif clicked == btn_open_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path.parent)))

    # Slots
    def _on_generate_quote(self) -> None:
        lines = self._collect_lines(self.quote_table)
        if not lines:
            QMessageBox.warning(self, 'Aucune ligne', 'Ajoutez au moins une ligne au devis.')
            return
        try:
            # Validité: parse YYYY-MM-DD si fourni
            vdate_txt = self.quote_validity.text().strip()
            vdate: date | None = None
            if vdate_txt:
                try:
                    y, m, d = [int(x) for x in vdate_txt.split('-')]
                    vdate = date(y, m, d)
                except Exception:
                    vdate = None
            json_path, pdf_path = self._controller.generate_document(
                DocumentType.QUOTE,
                self.quote_customer.text(),
                lines,
                subject=self.quote_subject.text() or None,
                validity_end_date=vdate,
                customer_address=self.quote_customer_address.text() or None,
                customer_email=self.quote_customer_email.text() or None,
                customer_phone=self.quote_customer_phone.text() or None,
                customer_siret=self.quote_customer_siret.text() or None,
            )
        except Exception as exc:  # pragma: no cover (UI feedback)
            QMessageBox.critical(
                self,
                'Erreur génération',
                f'Impossible de générer le devis:\n{exc!r}',
            )
            return
        self._show_generation_result(json_path, pdf_path)

    def _setup_quote_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form1 = QHBoxLayout()
        form1.addWidget(QLabel('Client:'))
        self.quote_customer = QLineEdit()
        form1.addWidget(self.quote_customer)
        layout.addLayout(form1)

        # Infos client (devis)
        grid_client = QGridLayout()
        grid_client.addWidget(QLabel('Adresse:'), 0, 0)
        self.quote_customer_address = QLineEdit()
        grid_client.addWidget(self.quote_customer_address, 0, 1)
        grid_client.addWidget(QLabel('Email:'), 1, 0)
        self.quote_customer_email = QLineEdit()
        grid_client.addWidget(self.quote_customer_email, 1, 1)
        grid_client.addWidget(QLabel('Téléphone:'), 2, 0)
        self.quote_customer_phone = QLineEdit()
        grid_client.addWidget(self.quote_customer_phone, 2, 1)
        grid_client.addWidget(QLabel('SIRET:'), 3, 0)
        self.quote_customer_siret = QLineEdit()
        grid_client.addWidget(self.quote_customer_siret, 3, 1)
        layout.addLayout(grid_client)

        # Bloc réalisation (Sujet + Validité)
        grid_real = QGridLayout()
        grid_real.addWidget(QLabel('Sujet:'), 0, 0)
        self.quote_subject = QLineEdit()
        grid_real.addWidget(self.quote_subject, 0, 1)
        grid_real.addWidget(QLabel('Validité (YYYY-MM-DD):'), 1, 0)
        self.quote_validity = QLineEdit()
        self.quote_validity.setPlaceholderText('ex: 2025-12-31')
        grid_real.addWidget(self.quote_validity, 1, 1)
        layout.addLayout(grid_real)

        self.quote_table = QTableWidget(0, 8)
        self.quote_table.setHorizontalHeaderLabels([
            'Item',
            'Description',
            'Unité',
            'Qté',
            'PU',
            'TVA %',
            '% Rem.',
            'Total HT',
        ])
        layout.addWidget(self.quote_table)

        # Totaux (live)
        totals_q = QHBoxLayout()
        self.quote_total_ht_label = QLabel('Total HT: 0.00 €')
        self.quote_total_tva_label = QLabel('Total TVA: 0.00 €')
        self.quote_total_net_label = QLabel('Net à payer: 0.00 €')
        totals_q.addWidget(self.quote_total_ht_label)
        totals_q.addWidget(self.quote_total_tva_label)
        totals_q.addWidget(self.quote_total_net_label)
        totals_q.addStretch(1)
        layout.addLayout(totals_q)

        btns = QHBoxLayout()
        add_btn = QPushButton('Ajouter ligne')
        add_btn.clicked.connect(lambda: self._add_line(self.quote_table))
        gen_btn = QPushButton('Générer le devis')
        gen_btn.clicked.connect(self._on_generate_quote)
        btns.addWidget(add_btn)
        btns.addStretch(1)
        btns.addWidget(gen_btn)
        layout.addLayout(btns)

        self.tabs.addTab(tab, 'Devis')
        # Recalcul des totaux quand le contenu d'une cellule (ex: description) change
        self.quote_table.itemChanged.connect(
            lambda _item: self._recompute_table_totals(self.quote_table)
        )

    def _on_generate_invoice(self) -> None:
        lines = self._collect_lines(self.invoice_table)
        if not lines:
            QMessageBox.warning(self, 'Aucune ligne', 'Ajoutez au moins une ligne à la facture.')
            return
        try:
            json_path, pdf_path = self._controller.generate_document(
                DocumentType.INVOICE,
                self.invoice_customer.text(),
                lines,
                customer_address=self.invoice_customer_address.text() or None,
                customer_email=self.invoice_customer_email.text() or None,
                customer_phone=self.invoice_customer_phone.text() or None,
                customer_siret=self.invoice_customer_siret.text() or None,
            )
        except Exception as exc:  # pragma: no cover (UI feedback)
            QMessageBox.critical(
                self,
                'Erreur génération',
                f'Impossible de générer la facture:\n{exc!r}',
            )
            return
        self._show_generation_result(json_path, pdf_path)

    def _populate_invoice_row(self, row: int, li: LineItem) -> None:
        combo = self.invoice_table.cellWidget(row, 0)
        if isinstance(combo, QComboBox):
            for i in range(combo.count()):
                data = combo.itemData(i)
                if isinstance(data, tuple) and data[0] == li.item_key:
                    combo.setCurrentIndex(i)
                    break
        # Description
        desc_item = self.invoice_table.item(row, 1)
        if isinstance(desc_item, QTableWidgetItem):
            desc_item.setText(li.description)
        # Unité
        unit_w = self.invoice_table.cellWidget(row, 2)
        if isinstance(unit_w, QComboBox):
            # Si l'unité n'est pas dans la liste, la renseigner en texte (combo éditable)
            idx = unit_w.findText(li.unit)
            if idx >= 0:
                unit_w.setCurrentIndex(idx)
            else:
                unit_w.setEditText(li.unit)
        # Quantité
        qty = self.invoice_table.cellWidget(row, 3)
        if isinstance(qty, QSpinBox):
            qty.setValue(int(li.quantity))
        # TVA %
        tax = self.invoice_table.cellWidget(row, 5)
        if isinstance(tax, QDoubleSpinBox):
            tax.setValue(float(li.tax_pct))
        # Remise
        disc = self.invoice_table.cellWidget(row, 6)
        if isinstance(disc, QDoubleSpinBox):
            disc.setValue(float(li.discount_pct))
        # Recalcul final de la ligne pour mettre à jour les totaux affichés
        self._recompute_row_totals(self.invoice_table, row)

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
            self._populate_invoice_row(self.invoice_table.rowCount() - 1, li)

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

        grid_client = QGridLayout()
        grid_client.addWidget(QLabel('Adresse:'), 0, 0)
        self.invoice_customer_address = QLineEdit()
        grid_client.addWidget(self.invoice_customer_address, 0, 1)
        grid_client.addWidget(QLabel('Email:'), 1, 0)
        self.invoice_customer_email = QLineEdit()
        grid_client.addWidget(self.invoice_customer_email, 1, 1)
        grid_client.addWidget(QLabel('Téléphone:'), 2, 0)
        self.invoice_customer_phone = QLineEdit()
        grid_client.addWidget(self.invoice_customer_phone, 2, 1)
        grid_client.addWidget(QLabel('SIRET:'), 3, 0)
        self.invoice_customer_siret = QLineEdit()
        grid_client.addWidget(self.invoice_customer_siret, 3, 1)
        layout.addLayout(grid_client)

        self.invoice_table = QTableWidget(0, 8)
        self.invoice_table.setHorizontalHeaderLabels([
            'Item',
            'Description',
            'Unité',
            'Qté',
            'PU',
            'TVA %',
            '% Rem.',
            'Total HT',
        ])
        layout.addWidget(self.invoice_table)

        # Totaux (live)
        totals_i = QHBoxLayout()
        self.invoice_total_ht_label = QLabel('Total HT: 0.00 €')
        self.invoice_total_tva_label = QLabel('Total TVA: 0.00 €')
        self.invoice_total_net_label = QLabel('Net à payer: 0.00 €')
        totals_i.addWidget(self.invoice_total_ht_label)
        totals_i.addWidget(self.invoice_total_tva_label)
        totals_i.addWidget(self.invoice_total_net_label)
        totals_i.addStretch(1)
        layout.addLayout(totals_i)

        btns = QHBoxLayout()
        add_btn = QPushButton('Ajouter ligne')
        add_btn.clicked.connect(lambda: self._add_line(self.invoice_table))
        gen_btn = QPushButton('Générer la facture')
        gen_btn.clicked.connect(self._on_generate_invoice)
        btns.addWidget(add_btn)
        btns.addStretch(1)
        btns.addWidget(gen_btn)
        layout.addLayout(btns)

        self.tabs.addTab(tab, 'Facture')
        self.invoice_table.itemChanged.connect(
            lambda _item: self._recompute_table_totals(self.invoice_table)
        )

    def _refresh_items_grid(self, grid: QGridLayout) -> None:
        items: list[tuple[str, str, float]] = sorted(
            self._controller.list_config_items(), key=lambda t: t[0]
        )
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

            # Bouton supprimer
            del_btn = QPushButton('Supprimer')

            def on_delete_bound(k_field: QLineEdit = key_edit, fallback_key: str = key) -> None:
                del_key = k_field.text().strip() or fallback_key
                self._controller.delete_item(del_key)
                self._rebuild_items_grid()

            # clicked(bool) émet un booléen; on le capture et on l'ignore
            del_btn.clicked.connect(lambda _checked=False, f=on_delete_bound: f())

            grid.addWidget(key_edit, row, 0)
            grid.addWidget(label_edit, row, 1)
            grid.addWidget(price_edit, row, 2)
            grid.addWidget(del_btn, row, 3)

    def _clear_items_grid(self, grid: QGridLayout) -> None:
        # Supprimer les widgets des lignes d'items (>=1), conserver l'entête (ligne 0)
        for i in reversed(range(grid.count())):
            li = grid.itemAt(i)
            if li is None:
                continue
            r = grid.getItemPosition(i)[0] or -1
            if r >= 1:
                w = li.widget() if hasattr(li, 'widget') else None
                if w is not None:
                    grid.removeWidget(w)
                    w.deleteLater()
                else:
                    grid.removeItem(li)

    def _rebuild_items_grid(self) -> None:
        if hasattr(self, 'items_grid') and isinstance(self.items_grid, QGridLayout):
            self._clear_items_grid(self.items_grid)
            self._refresh_items_grid(self.items_grid)

    def _create_company_box(self) -> QGroupBox:
        company_box = QGroupBox('Société émettrice')
        g = QGridLayout(company_box)
        g.addWidget(QLabel('Nom:'), 0, 0)
        self.company_name = QLineEdit(self._controller.get_company_name())
        self.company_name.editingFinished.connect(
            lambda: self._controller.set_company_name(self.company_name.text())
        )
        g.addWidget(self.company_name, 0, 1)

        # Logo
        g.addWidget(QLabel('Logo:'), 1, 0)
        self.company_logo = QLineEdit(self._controller.get_company_logo_path() or '')
        browse_btn = QPushButton('Parcourir…')
        preview = QLabel()
        preview.setMinimumHeight(60)

        def on_browse_logo() -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                'Choisir un logo',
                '',
                'Images (*.png *.jpg *.jpeg)',
            )
            if path:
                self.company_logo.setText(path)
                self._controller.set_company_logo_path(path)
                _update_preview()

        def on_logo_edit_finished() -> None:
            self._controller.set_company_logo_path(self.company_logo.text() or None)
            _update_preview()

        def _update_preview() -> None:
            p = self.company_logo.text().strip()
            if not p:
                preview.clear()
                return
            pix = QPixmap(p)
            if pix.isNull():
                preview.setText('(aperçu indisponible)')
                return
            w = float(self.logo_width.value()) if hasattr(self, 'logo_width') else 60.0
            h = float(self.logo_height.value()) if hasattr(self, 'logo_height') else w
            scaled = pix.scaled(int(w), int(h), Qt.AspectRatioMode.KeepAspectRatio)
            preview.setPixmap(scaled)

        browse_btn.clicked.connect(on_browse_logo)
        self.company_logo.editingFinished.connect(on_logo_edit_finished)
        g.addWidget(self.company_logo, 1, 1)
        g.addWidget(browse_btn, 1, 2)
        g.addWidget(preview, 2, 1, 1, 2)

        # Largeur max logo
        g.addWidget(QLabel('Largeur logo (px):'), 3, 0)
        self.logo_width = QDoubleSpinBox()
        self.logo_width.setRange(20.0, 400.0)
        self.logo_width.setDecimals(0)
        self.logo_width.setValue(float(self._controller.get_company_logo_max_width() or 60.0))

        def on_logo_width_changed() -> None:
            self._controller.set_company_logo_max_width(float(self.logo_width.value()))
            _update_preview()

        self.logo_width.valueChanged.connect(on_logo_width_changed)
        g.addWidget(self.logo_width, 3, 1)
        _update_preview()

        # Hauteur max logo
        g.addWidget(QLabel('Hauteur logo (px):'), 4, 0)
        self.logo_height = QDoubleSpinBox()
        self.logo_height.setRange(20.0, 400.0)
        self.logo_height.setDecimals(0)
        self.logo_height.setValue(
            float(self._controller.get_company_logo_max_height() or self.logo_width.value())
        )

        def on_logo_height_changed() -> None:
            self._controller.set_company_logo_max_height(float(self.logo_height.value()))
            _update_preview()

        self.logo_height.valueChanged.connect(on_logo_height_changed)
        g.addWidget(self.logo_height, 4, 1)

        # Marge droite logo
        g.addWidget(QLabel('Marge droite logo (px):'), 5, 0)
        self.logo_margin = QDoubleSpinBox()
        self.logo_margin.setRange(0.0, 200.0)
        self.logo_margin.setDecimals(0)
        self.logo_margin.setValue(float(self._controller.get_company_logo_margin_right() or 20.0))

        def on_logo_margin_changed() -> None:
            self._controller.set_company_logo_margin_right(float(self.logo_margin.value()))
            _update_preview()

        self.logo_margin.valueChanged.connect(on_logo_margin_changed)
        g.addWidget(self.logo_margin, 5, 1)

        # Coordonnées société
        g.addWidget(QLabel('Adresse:'), 6, 0)
        self.company_address = QLineEdit(self._controller.get_company_address() or '')
        self.company_address.editingFinished.connect(
            lambda: self._controller.set_company_address(self.company_address.text() or None)
        )
        g.addWidget(self.company_address, 6, 1, 1, 2)

        g.addWidget(QLabel('Email:'), 7, 0)
        self.company_email = QLineEdit(self._controller.get_company_email() or '')
        self.company_email.editingFinished.connect(
            lambda: self._controller.set_company_email(self.company_email.text() or None)
        )
        g.addWidget(self.company_email, 7, 1, 1, 2)

        g.addWidget(QLabel('Téléphone:'), 8, 0)
        self.company_phone = QLineEdit(self._controller.get_company_phone() or '')
        self.company_phone.editingFinished.connect(
            lambda: self._controller.set_company_phone(self.company_phone.text() or None)
        )
        g.addWidget(self.company_phone, 8, 1, 1, 2)

        g.addWidget(QLabel('SIRET:'), 9, 0)
        self.company_siret = QLineEdit(self._controller.get_company_siret() or '')
        self.company_siret.editingFinished.connect(
            lambda: self._controller.set_company_siret(self.company_siret.text() or None)
        )
        g.addWidget(self.company_siret, 9, 1, 1, 2)
        return company_box

    def _create_items_box(self) -> QGroupBox:
        items_box = QGroupBox('Produits/Services')
        gi = QGridLayout(items_box)
        self.items_grid = gi
        gi.addWidget(QLabel('Clé'), 0, 0)
        gi.addWidget(QLabel('Libellé'), 0, 1)
        gi.addWidget(QLabel('Prix unitaire'), 0, 2)
        gi.addWidget(QLabel(''), 0, 3)
        self._refresh_items_grid(gi)
        return items_box

    def _create_add_item_box(self) -> QGroupBox:
        add_box = QGroupBox('Ajouter un item')
        add_layout = QHBoxLayout(add_box)
        self.add_item_key = QLineEdit()
        self.add_item_key.setPlaceholderText('clé (ex: svc)')
        self.add_item_label = QLineEdit()
        self.add_item_label.setPlaceholderText('libellé')
        self.add_item_price = QDoubleSpinBox()
        self.add_item_price.setRange(0.0, 10_000_000.0)
        self.add_item_price.setDecimals(2)
        add_btn = QPushButton('Ajouter')

        def on_add_item() -> None:
            key = self.add_item_key.text().strip()
            label = self.add_item_label.text().strip()
            price = float(self.add_item_price.value())
            if not key or not label:
                return
            self._controller.upsert_item(key, label, price)
            # reset et rafraîchir la grille
            self.add_item_key.clear()
            self.add_item_label.clear()
            self.add_item_price.setValue(0.0)
            self._rebuild_items_grid()

        add_btn.clicked.connect(on_add_item)
        add_layout.addWidget(QLabel('Clé:'))
        add_layout.addWidget(self.add_item_key)
        add_layout.addWidget(QLabel('Libellé:'))
        add_layout.addWidget(self.add_item_label)
        add_layout.addWidget(QLabel('Prix:'))
        add_layout.addWidget(self.add_item_price)
        add_layout.addStretch(1)
        add_layout.addWidget(add_btn)
        return add_box

    def _setup_config_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(self._create_company_box())
        layout.addWidget(self._create_items_box())
        layout.addWidget(self._create_add_item_box())

        self.tabs.addTab(tab, 'Configuration')

    def __init__(self, controller: _ControllerProto) -> None:
        """Initialize the main window and its tabs."""
        super().__init__()
        self._controller = controller
        self.setWindowTitle('Générateur de devis/factures')
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._setup_quote_tab()
        self._setup_invoice_tab()
        self._setup_config_tab()
