"""Boîte de dialogue des préférences utilisateur."""

import json
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QGroupBox, QFormLayout,
    QCheckBox, QSpinBox, QLineEdit, QComboBox, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt

from core.ollama_engine import DEFAULT_MODEL, OLLAMA_BASE_URL
from ui.theme import DARK, LIGHT, load_theme, save_theme

from config import CONFIG_DIR

logger = logging.getLogger(__name__)

SETTINGS_FILE = CONFIG_DIR / "settings.json"

_DEFAULTS = {
    "clipboard_monitor": False,
    "max_history": 500,
    "tts_speed": 145,
    "ollama_model": DEFAULT_MODEL,
}


def load_settings() -> dict:
    """Charge les préférences depuis le fichier JSON (valeurs par défaut si absent)."""
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **data}
        except Exception as e:
            logger.warning(f"Impossible de lire les préférences : {e}")
    return dict(_DEFAULTS)


def save_settings(settings: dict):
    """Persiste les préférences dans le fichier JSON."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Préférences — LibreTrador")
        self.setMinimumWidth(420)
        self._settings = load_settings()
        self._setup_ui()

    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- Interface / Thème ---
        ui_group = QGroupBox("Interface")
        ui_form = QFormLayout(ui_group)
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("🌙 Sombre", DARK)
        self._theme_combo.addItem("☀ Clair", LIGHT)
        current_theme = load_theme()
        self._theme_combo.setCurrentIndex(0 if current_theme == DARK else 1)
        ui_form.addRow("Thème :", self._theme_combo)
        layout.addWidget(ui_group)

        # --- Presse-papier ---
        cb_group = QGroupBox("Presse-papier")
        cb_layout = QVBoxLayout(cb_group)
        self._cb_monitor = QCheckBox("Surveiller le presse-papier (texte anglais détecté)")
        self._cb_monitor.setChecked(self._settings["clipboard_monitor"])
        cb_layout.addWidget(self._cb_monitor)
        note = QLabel(
            "<i>Détecte automatiquement un texte anglais copié et propose la traduction.</i>"
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 10px;")
        cb_layout.addWidget(note)
        layout.addWidget(cb_group)

        # --- Historique ---
        hist_group = QGroupBox("Historique")
        hist_form = QFormLayout(hist_group)
        self._max_hist = QSpinBox()
        self._max_hist.setRange(10, 5000)
        self._max_hist.setValue(self._settings["max_history"])
        self._max_hist.setSuffix(" entrées")
        hist_form.addRow("Limite :", self._max_hist)
        layout.addWidget(hist_group)

        # --- Ollama ---
        ollama_group = QGroupBox("Moteur Ollama (LLM local)")
        ollama_form = QFormLayout(ollama_group)
        self._ollama_model = QLineEdit(self._settings["ollama_model"])
        self._ollama_model.setPlaceholderText(DEFAULT_MODEL)
        self._ollama_model.setToolTip(
            "Nom du modèle Ollama à utiliser pour la traduction.\n"
            f"Modèle recommandé : {DEFAULT_MODEL}\n"
            f"URL API : {OLLAMA_BASE_URL}/api/generate"
        )
        ollama_form.addRow("Modèle :", self._ollama_model)
        note_ollama = QLabel(
            f"<i>Modèle recommandé : <b>{DEFAULT_MODEL}</b>  —  "
            f"Ollama doit tourner sur <tt>{OLLAMA_BASE_URL}</tt></i>"
        )
        note_ollama.setWordWrap(True)
        note_ollama.setStyleSheet("color: gray; font-size: 10px;")
        ollama_form.addRow(note_ollama)
        layout.addWidget(ollama_group)

        # --- Synthèse vocale ---
        tts_group = QGroupBox("Synthèse vocale (espeak-ng)")
        tts_form = QFormLayout(tts_group)
        self._tts_speed = QSpinBox()
        self._tts_speed.setRange(80, 400)
        self._tts_speed.setValue(self._settings["tts_speed"])
        self._tts_speed.setSuffix(" mots/min")
        tts_form.addRow("Vitesse :", self._tts_speed)
        layout.addWidget(tts_group)

        # --- Boutons ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        ok = QPushButton("OK")
        ok.setDefault(True)
        ok.clicked.connect(self._save_and_accept)
        btn_row.addWidget(ok)

        cancel = QPushButton("Annuler")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------

    def _save_and_accept(self):
        self._settings["clipboard_monitor"] = self._cb_monitor.isChecked()
        self._settings["max_history"] = self._max_hist.value()
        self._settings["tts_speed"] = self._tts_speed.value()
        model = self._ollama_model.text().strip()
        self._settings["ollama_model"] = model if model else DEFAULT_MODEL
        save_theme(self._theme_combo.currentData())
        save_settings(self._settings)
        self.accept()

    def get_settings(self) -> dict:
        return dict(self._settings)
