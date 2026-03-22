"""Dialogue de gestion du glossaire personnalisé."""

import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QCheckBox, QFileDialog,
    QMessageBox, QAbstractItemView,
)
from PyQt6.QtCore import Qt

from core.glossary import load_glossary, save_glossary, glossary_path

logger = logging.getLogger(__name__)

# Indices des colonnes
_COL_ENABLED    = 0
_COL_TERM       = 1
_COL_REPLACEMENT = 2
_COL_WHOLE_WORD = 3
_COL_CASE_SENS  = 4


class GlossaryDialog(QDialog):
    """Fenêtre de gestion du glossaire pour une direction de traduction."""

    def __init__(self, src_lang: str = "en", tgt_lang: str = "fr", parent=None):
        super().__init__(parent)
        self._src_lang = src_lang
        self._tgt_lang = tgt_lang
        direction = f"{src_lang.upper()}→{tgt_lang.upper()}"
        self.setWindowTitle(f"Glossaire personnalisé — {direction}")
        self.setMinimumSize(780, 460)
        self._setup_ui(direction)
        self._load()

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _setup_ui(self, direction: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Explication
        info = QLabel(
            f"<b>Règles de remplacement post-traduction ({direction})</b><br>"
            "Ces règles sont appliquées <i>après</i> la traduction, dans l'ordre affiché.<br>"
            f"Fichier : <code>{glossary_path(self._src_lang, self._tgt_lang)}</code>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tableau des règles
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["✓", "Terme à rechercher", "Remplacer par", "Mot entier", "Casse exacte"]
        )
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(_COL_ENABLED,     QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_COL_TERM,        QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(_COL_REPLACEMENT, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(_COL_WHOLE_WORD,  QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(_COL_CASE_SENS,   QHeaderView.ResizeMode.ResizeToContents)

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # Boutons de gestion des règles
        rules_bar = QHBoxLayout()

        add_btn = QPushButton("＋ Ajouter une règle")
        add_btn.clicked.connect(self._add_row)
        rules_bar.addWidget(add_btn)

        del_btn = QPushButton("− Supprimer la sélection")
        del_btn.clicked.connect(self._delete_selected)
        rules_bar.addWidget(del_btn)

        rules_bar.addStretch()

        up_btn = QPushButton("↑")
        up_btn.setToolTip("Monter la règle sélectionnée")
        up_btn.setFixedWidth(36)
        up_btn.clicked.connect(self._move_up)
        rules_bar.addWidget(up_btn)

        down_btn = QPushButton("↓")
        down_btn.setToolTip("Descendre la règle sélectionnée")
        down_btn.setFixedWidth(36)
        down_btn.clicked.connect(self._move_down)
        rules_bar.addWidget(down_btn)

        layout.addLayout(rules_bar)

        # Import / Export
        io_bar = QHBoxLayout()

        import_btn = QPushButton("📂 Importer JSON")
        import_btn.setToolTip("Importer des règles depuis un fichier JSON")
        import_btn.clicked.connect(self._import_json)
        io_bar.addWidget(import_btn)

        export_btn = QPushButton("💾 Exporter JSON")
        export_btn.setToolTip("Exporter les règles dans un fichier JSON")
        export_btn.clicked.connect(self._export_json)
        io_bar.addWidget(export_btn)

        io_bar.addStretch()
        layout.addLayout(io_bar)

        # OK / Annuler
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._save_and_accept)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Chargement / sauvegarde
    # ------------------------------------------------------------------

    def _load(self):
        rules = load_glossary(self._src_lang, self._tgt_lang)
        self._table.setRowCount(0)
        for rule in rules:
            self._append_row(
                term=rule.get("term", ""),
                replacement=rule.get("replacement", ""),
                enabled=rule.get("enabled", True),
                whole_word=rule.get("whole_word", True),
                case_sensitive=rule.get("case_sensitive", False),
            )

    def _save_and_accept(self):
        save_glossary(self._collect_rules(), self._src_lang, self._tgt_lang)
        self.accept()

    def _collect_rules(self) -> list[dict]:
        rules = []
        for row in range(self._table.rowCount()):
            term_item = self._table.item(row, _COL_TERM)
            repl_item = self._table.item(row, _COL_REPLACEMENT)
            term = term_item.text().strip() if term_item else ""
            if not term:
                continue
            rules.append({
                "term":           term,
                "replacement":    repl_item.text() if repl_item else "",
                "enabled":        self._get_check(row, _COL_ENABLED),
                "whole_word":     self._get_check(row, _COL_WHOLE_WORD),
                "case_sensitive": self._get_check(row, _COL_CASE_SENS),
            })
        return rules

    # ------------------------------------------------------------------
    # Helpers tableau
    # ------------------------------------------------------------------

    def _append_row(self, term: str = "", replacement: str = "",
                    enabled: bool = True, whole_word: bool = True,
                    case_sensitive: bool = False):
        row = self._table.rowCount()
        self._table.insertRow(row)

        self._set_check(row, _COL_ENABLED,    enabled)
        self._table.setItem(row, _COL_TERM,        QTableWidgetItem(term))
        self._table.setItem(row, _COL_REPLACEMENT, QTableWidgetItem(replacement))
        self._set_check(row, _COL_WHOLE_WORD, whole_word)
        self._set_check(row, _COL_CASE_SENS,  case_sensitive)

    def _set_check(self, row: int, col: int, checked: bool):
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
                      | Qt.ItemFlag.ItemIsSelectable)
        item.setCheckState(
            Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, col, item)

    def _get_check(self, row: int, col: int) -> bool:
        item = self._table.item(row, col)
        if item is None:
            return False
        return item.checkState() == Qt.CheckState.Checked

    # ------------------------------------------------------------------
    # Actions boutons
    # ------------------------------------------------------------------

    def _add_row(self):
        self._append_row()
        row = self._table.rowCount() - 1
        self._table.scrollToBottom()
        self._table.setCurrentCell(row, _COL_TERM)
        self._table.editItem(self._table.item(row, _COL_TERM))

    def _delete_selected(self):
        rows = sorted(
            {idx.row() for idx in self._table.selectedIndexes()},
            reverse=True,
        )
        for row in rows:
            self._table.removeRow(row)

    def _move_up(self):
        row = self._table.currentRow()
        if row <= 0:
            return
        self._swap_rows(row, row - 1)
        self._table.setCurrentCell(row - 1, self._table.currentColumn())

    def _move_down(self):
        row = self._table.currentRow()
        if row < 0 or row >= self._table.rowCount() - 1:
            return
        self._swap_rows(row, row + 1)
        self._table.setCurrentCell(row + 1, self._table.currentColumn())

    def _swap_rows(self, a: int, b: int):
        """Échange les données de deux lignes."""
        for col in range(self._table.columnCount()):
            item_a = self._table.takeItem(a, col)
            item_b = self._table.takeItem(b, col)
            self._table.setItem(a, col, item_b)
            self._table.setItem(b, col, item_a)

    # ------------------------------------------------------------------
    # Import / Export JSON
    # ------------------------------------------------------------------

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer un glossaire JSON",
            str(Path.home()), "JSON (*.json)"
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Le fichier doit contenir une liste JSON.")
            reply = QMessageBox.question(
                self, "Importer",
                f"{len(data)} règle(s) trouvée(s).\nAjouter aux règles existantes ?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.No:
                self._table.setRowCount(0)
            for rule in data:
                if isinstance(rule, dict) and rule.get("term"):
                    self._append_row(
                        term=rule.get("term", ""),
                        replacement=rule.get("replacement", ""),
                        enabled=rule.get("enabled", True),
                        whole_word=rule.get("whole_word", True),
                        case_sensitive=rule.get("case_sensitive", False),
                    )
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'import", str(e))

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le glossaire",
            str(Path.home() / f"glossaire_{self._src_lang}_{self._tgt_lang}.json"),
            "JSON (*.json)"
        )
        if not path:
            return
        try:
            rules = self._collect_rules()
            Path(path).write_text(
                json.dumps(rules, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            QMessageBox.information(
                self, "Export réussi",
                f"{len(rules)} règle(s) exportée(s) vers\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'export", str(e))
