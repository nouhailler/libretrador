#!/usr/bin/env python3
"""
LibreTrador — Traducteur hors-ligne Anglais → Français.
Point d'entrée principal.
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.QtGui import QIcon

from config import APP_NAME, APP_VERSION, DATA_DIR, CONFIG_DIR, LOG_FILE


def _setup_dirs():
    for d in (DATA_DIR, CONFIG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def main():
    _setup_dirs()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("libretrador")
    # Ne pas quitter quand la fenêtre est masquée (mode tray)
    app.setQuitOnLastWindowClosed(True)

    from ui.theme import apply_theme, load_theme
    apply_theme(app, load_theme())

    _setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Démarrage de {APP_NAME} v{APP_VERSION}")

    # Icône globale
    icon_path = Path(__file__).parent / "assets" / "libretrador_48.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # --- Vérification du modèle Argos ---
    from core.translator import is_model_installed
    from ui.model_manager import ModelManagerDialog

    if not is_model_installed():
        logger.info("Modèle EN→FR absent — affichage du dialogue d'installation")
        dlg = ModelManagerDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            QMessageBox.critical(
                None,
                APP_NAME,
                "Le modèle de traduction EN→FR est requis.\n"
                "LibreTrador ne peut pas démarrer sans lui.",
            )
            sys.exit(1)

    # --- Fenêtre principale ---
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
