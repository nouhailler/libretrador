"""Widget panneau source ou cible (les deux sont éditables)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLabel, QPushButton, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QTextCursor

from config import MAX_CHARS
from core.synonyms import get_synonyms


class _SynonymTextEdit(QTextEdit):
    """QTextEdit avec menu contextuel enrichi de synonymes WordNet."""

    def __init__(self, lang: str = "en", parent=None):
        super().__init__(parent)
        self.lang = lang  # 'en' ou 'fr' — mis à jour par TextPanel.set_lang()

    def contextMenuEvent(self, event):
        # 1. Mot sous le curseur
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()

        # 2. Menu standard Qt (couper / copier / coller / …)
        menu = self.createStandardContextMenu()

        if word and word.isalpha():
            menu.addSeparator()

            # Titre non-cliquable
            title_act = QAction(f'Synonymes de « {word} »', self)
            title_act.setEnabled(False)
            font = title_act.font()
            font.setBold(True)
            title_act.setFont(font)
            menu.addAction(title_act)

            synonymes = get_synonyms(word, self.lang)

            if synonymes:
                for syn in synonymes:
                    act = QAction(f"  • {syn}", self)
                    act.triggered.connect(
                        lambda checked, s=syn, c=cursor: self._replace_word(c, s)
                    )
                    menu.addAction(act)
            else:
                no_act = QAction("  (aucun synonyme trouvé)", self)
                no_act.setEnabled(False)
                menu.addAction(no_act)

        menu.exec(event.globalPos())

    def _replace_word(self, cursor: QTextCursor, synonym: str):
        cursor.insertText(synonym)


class TextPanel(QWidget):
    """
    Panneau de texte réutilisable pour la source et la cible.
    Les deux panneaux sont éditables.

    Signaux :
      text_changed(str)   — émis à chaque frappe (panneau source)
      copy_requested()    — clic sur "Copier" (panneau cible)
      listen_requested()  — clic sur "Écouter" (panneau cible)
      clear_requested()   — clic sur "✖" dans l'en-tête
    """

    text_changed     = pyqtSignal(str)
    copy_requested   = pyqtSignal()
    listen_requested = pyqtSignal()
    clear_requested  = pyqtSignal()

    # readonly=True : panneau cible (pas de compteur, boutons Écouter+Copier)
    # readonly=False : panneau source (compteur de caractères)
    # Les deux sont éditables dans tous les cas.

    def __init__(self, title: str, readonly: bool = False,
                 lang: str = "en", parent=None):
        super().__init__(parent)
        self._readonly = readonly
        self._setup_ui(title, lang)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def _setup_ui(self, title: str, lang: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # En-tête : titre + bouton ✖ effacer ce panneau
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(QFont(None, 10, QFont.Weight.Bold))
        header.addWidget(self._title_lbl)
        header.addStretch()

        self._clear_btn = QPushButton("✖")
        self._clear_btn.setToolTip("Effacer ce panneau")
        self._clear_btn.setFixedSize(22, 22)
        self._clear_btn.setStyleSheet(
            "QPushButton { border: none; color: gray; font-size: 11px; padding: 0; }"
            "QPushButton:hover { color: #f44336; }"
        )
        self._clear_btn.clicked.connect(self._on_clear)
        header.addWidget(self._clear_btn)

        layout.addLayout(header)

        # Zone de texte avec menu synonymes
        self._edit = _SynonymTextEdit(lang=lang)
        self._edit.setFont(QFont("Noto Sans", 11))
        self._edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._edit.setPlaceholderText(
            "Saisissez du texte anglais ici…"
            if not self._readonly
            else "La traduction apparaîtra ici…"
        )
        if not self._readonly:
            self._edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._edit)

        # Pied de page
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)

        if not self._readonly:
            self._counter = QLabel(f"0 / {MAX_CHARS} car.")
            self._counter.setStyleSheet("color: gray; font-size: 10px;")
            footer.addWidget(self._counter)
            footer.addStretch()
        else:
            footer.addStretch()
            self._listen_btn = QPushButton("🔊 Écouter")
            self._listen_btn.setMaximumWidth(110)
            self._listen_btn.clicked.connect(self.listen_requested)
            footer.addWidget(self._listen_btn)

            self._copy_btn = QPushButton("📋 Copier")
            self._copy_btn.setMaximumWidth(100)
            self._copy_btn.clicked.connect(self.copy_requested)
            footer.addWidget(self._copy_btn)

        layout.addLayout(footer)

    # ------------------------------------------------------------------
    # Slots privés
    # ------------------------------------------------------------------

    def _on_text_changed(self):
        text = self._edit.toPlainText()
        count = len(text)
        if count > MAX_CHARS:
            color = "#f44336"
        elif count > int(MAX_CHARS * 0.8):
            color = "#ff9800"
        else:
            color = "gray"
        self._counter.setText(f"{count} / {MAX_CHARS} car.")
        self._counter.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.text_changed.emit(text)

    def _on_clear(self):
        self._edit.clear()
        self.reset_border()
        self.clear_requested.emit()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def get_text(self) -> str:
        return self._edit.toPlainText()

    def set_text(self, text: str):
        self._edit.setPlainText(text)

    def clear(self):
        self._edit.clear()

    def set_border_success(self, success: bool = True):
        color = "#4caf50" if success else "#f44336"
        self._edit.setStyleSheet(f"border: 2px solid {color};")

    def reset_border(self):
        self._edit.setStyleSheet("")

    def set_listen_active(self, active: bool):
        if hasattr(self, "_listen_btn"):
            self._listen_btn.setText("⏹ Stop" if active else "🔊 Écouter")

    def set_listen_enabled(self, enabled: bool):
        if hasattr(self, "_listen_btn"):
            self._listen_btn.setEnabled(enabled)

    def set_title(self, title: str):
        self._title_lbl.setText(title)

    def set_placeholder(self, text: str):
        self._edit.setPlaceholderText(text)

    def set_lang(self, lang: str):
        """Met à jour la langue pour la recherche de synonymes ('en' ou 'fr')."""
        self._edit.lang = lang
