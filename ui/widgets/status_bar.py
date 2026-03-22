"""Barre de statut personnalisée avec infos moteur/modèle/version."""

from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt
from config import APP_VERSION


class AppStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(False)

        self._engine_label = QLabel("○ Moteur : Argos EN→FR")
        self._model_label  = QLabel("Modèle : —")
        self._version_label = QLabel(f"v{APP_VERSION}")

        self.addPermanentWidget(self._engine_label)
        self.addPermanentWidget(_separator())
        self.addPermanentWidget(self._model_label)
        self.addPermanentWidget(_separator())
        self.addPermanentWidget(self._version_label)

    # ------------------------------------------------------------------
    def set_engine_ready(self, ready: bool, engine: str = "Argos",
                         direction: str = "EN→FR"):
        if ready:
            self._engine_label.setText(f"● Moteur : {engine} {direction}")
            self._engine_label.setStyleSheet("color: #4caf50;")
        else:
            self._engine_label.setText("○ Moteur : non prêt")
            self._engine_label.setStyleSheet("color: #f44336;")

    def set_model_version(self, version: str):
        self._model_label.setText(f"Modèle : {version}")

    def set_status(self, message: str, timeout: int = 3000):
        self.showMessage(message, timeout)


def _separator() -> QLabel:
    lbl = QLabel(" | ")
    lbl.setStyleSheet("color: gray;")
    return lbl
