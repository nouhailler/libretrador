"""Dialogue de téléchargement et d'installation d'un modèle Argos."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

logger = logging.getLogger(__name__)


class _DownloadWorker(QThread):
    progress = pyqtSignal(int)           # 0-100
    status   = pyqtSignal(str)           # message textuel
    finished = pyqtSignal(bool, str)     # (succès, message)

    def __init__(self, src_code: str = "en", tgt_code: str = "fr", parent=None):
        super().__init__(parent)
        self.src_code = src_code
        self.tgt_code = tgt_code

    def run(self):
        try:
            from argostranslate import package

            arrow = f"{self.src_code.upper()}→{self.tgt_code.upper()}"
            self.status.emit("Mise à jour de l'index des paquets Argos…")
            self.progress.emit(10)
            package.update_package_index()

            self.status.emit(f"Recherche du modèle {arrow}…")
            self.progress.emit(20)
            available = package.get_available_packages()
            pkg = next(
                (p for p in available
                 if p.from_code == self.src_code and p.to_code == self.tgt_code),
                None,
            )
            if pkg is None:
                self.finished.emit(False, f"Modèle {arrow} introuvable dans l'index Argos.")
                return

            self.status.emit(
                f"Téléchargement du modèle ({pkg.from_name} → {pkg.to_name})…"
                "\nCela peut prendre quelques minutes (~100 Mo)."
            )
            self.progress.emit(30)
            download_path = pkg.download()

            self.status.emit("Installation du modèle…")
            self.progress.emit(90)
            package.install_from_path(download_path)

            self.progress.emit(100)
            self.finished.emit(True, f"✓ Modèle {arrow} installé avec succès !")

        except Exception as e:
            logger.error(f"Erreur téléchargement modèle : {e}")
            self.finished.emit(False, f"Erreur : {e}")


class ModelManagerDialog(QDialog):
    """Dialogue affiché si un modèle Argos est absent."""

    def __init__(self, src_code: str = "en", tgt_code: str = "fr",
                 src_name: str = "Anglais", tgt_name: str = "Français",
                 parent=None):
        super().__init__(parent)
        self._src_code = src_code
        self._tgt_code = tgt_code
        self._src_name = src_name
        self._tgt_name = tgt_name
        arrow = f"{src_name} → {tgt_name}"
        self.setWindowTitle(f"LibreTrador — Installation du modèle {arrow}")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._worker = None
        self._setup_ui(arrow)

    def _setup_ui(self, arrow: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            f"<b>Modèle de traduction {arrow} requis</b><br><br>"
            "LibreTrador utilise <b>Argos Translate</b> pour la traduction hors-ligne.<br>"
            f"Le modèle {arrow} (~100 Mo) doit être téléchargé une seule fois<br>"
            "et sera stocké dans votre répertoire utilisateur.<br><br>"
            "Cliquez sur <b>Télécharger</b> pour continuer."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(info)

        self._status_lbl = QLabel("")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setMinimumHeight(40)
        layout.addWidget(self._status_lbl)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        buttons = QHBoxLayout()

        self._dl_btn = QPushButton("⬇  Télécharger")
        self._dl_btn.setDefault(True)
        self._dl_btn.clicked.connect(self._start_download)
        buttons.addWidget(self._dl_btn)

        self._cancel_btn = QPushButton("Annuler")
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)

        layout.addLayout(buttons)

    # ------------------------------------------------------------------

    def _start_download(self):
        self._dl_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_lbl.setText("Démarrage…")
        self._status_lbl.setStyleSheet("")

        self._worker = _DownloadWorker(self._src_code, self._tgt_code, self)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.status.connect(self._status_lbl.setText)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, success: bool, message: str):
        self._status_lbl.setText(message)
        if success:
            self._status_lbl.setStyleSheet("color: #4caf50;")
            self._dl_btn.setText("✓ Installé")
            self._cancel_btn.setText("Démarrer LibreTrador")
            try:
                self._cancel_btn.clicked.disconnect()
            except TypeError:
                pass
            self._cancel_btn.clicked.connect(self.accept)
        else:
            self._status_lbl.setStyleSheet("color: #f44336;")
            self._dl_btn.setEnabled(True)
            self._dl_btn.setText("⬇  Réessayer")
