"""Fenêtre historique des traductions avec recherche full-text."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QPushButton, QLabel, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.database import get_history, delete_entry, clear_history

logger = logging.getLogger(__name__)


class HistoryWindow(QDialog):
    """
    Fenêtre listant l'historique SQLite.
    Double-clic → émet translation_selected(source, target) et se ferme.
    """

    translation_selected = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des traductions")
        self.setMinimumSize(860, 520)
        self._setup_ui()
        self._load()

    # ------------------------------------------------------------------
    # Construction UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Barre de recherche
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher dans l'historique…")
        self._search.textChanged.connect(lambda t: self._load(search=t or None))
        search_row.addWidget(self._search)

        clear_all_btn = QPushButton("🗑  Tout effacer")
        clear_all_btn.clicked.connect(self._clear_all)
        search_row.addWidget(clear_all_btn)
        layout.addLayout(search_row)

        # Tableau
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Direction", "Source", "Traduction", "id"]
        )
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnHidden(4, True)          # colonne id cachée
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Compte
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self._count_lbl)

        # Boutons du bas
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        del_btn = QPushButton("🗑  Supprimer la sélection")
        del_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(del_btn)

        close_btn = QPushButton("Fermer")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def _load(self, search: str = None):
        entries = get_history(limit=300, search=search)
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            ts = entry["timestamp"][:19].replace("T", " ")
            src = entry["source_text"]
            tgt = entry["target_text"]
            direction = entry.get("direction") or (
                f"{entry.get('source_lang','en')}→{entry.get('target_lang','fr')}"
            )

            item_ts  = QTableWidgetItem(ts)
            item_dir = QTableWidgetItem(direction.upper())
            item_src = QTableWidgetItem(src[:120] + ("…" if len(src) > 120 else ""))
            item_tgt = QTableWidgetItem(tgt[:120] + ("…" if len(tgt) > 120 else ""))
            item_id  = QTableWidgetItem(str(entry["id"]))

            item_dir.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Stocker le texte complet dans UserRole pour le double-clic
            item_src.setData(Qt.ItemDataRole.UserRole, src)
            item_tgt.setData(Qt.ItemDataRole.UserRole, tgt)

            self._table.setItem(row, 0, item_ts)
            self._table.setItem(row, 1, item_dir)
            self._table.setItem(row, 2, item_src)
            self._table.setItem(row, 3, item_tgt)
            self._table.setItem(row, 4, item_id)

        self._table.setSortingEnabled(True)
        word = "entrée" if len(entries) == 1 else "entrées"
        self._count_lbl.setText(f"{len(entries)} {word} dans l'historique")

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def _on_double_click(self, index):
        row = index.row()
        src_item = self._table.item(row, 2)
        tgt_item = self._table.item(row, 3)
        if src_item and tgt_item:
            src = src_item.data(Qt.ItemDataRole.UserRole) or src_item.text()
            tgt = tgt_item.data(Qt.ItemDataRole.UserRole) or tgt_item.text()
            self.translation_selected.emit(src, tgt)
            self.close()

    def _delete_selected(self):
        rows = sorted(
            {idx.row() for idx in self._table.selectedIndexes()},
            reverse=True,
        )
        if not rows:
            return
        for row in rows:
            id_item = self._table.item(row, 4)
            if id_item:
                delete_entry(int(id_item.text()))
        self._load(search=self._search.text() or None)

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            "Effacer tout l'historique des traductions ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_history()
            self._load()
