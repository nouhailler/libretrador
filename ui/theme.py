"""
Thèmes visuels de LibreTrador — dark & light.

Usage :
    from ui.theme import apply_theme, load_theme, save_theme, DARK, LIGHT
    apply_theme(app, load_theme())
"""

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

DARK  = "dark"
LIGHT = "light"

# ──────────────────────────────────────────────────────────────────────
# Palettes
# ──────────────────────────────────────────────────────────────────────

_PALETTES: dict[str, dict] = {
    DARK: {
        "bg_primary":     "#1e1e2e",
        "bg_secondary":   "#252535",
        "bg_tertiary":    "#2a2a3d",
        "accent":         "#7c6af7",
        "accent_hover":   "#6c5ce7",
        "success":        "#a8e063",
        "error":          "#f38ba8",
        "text_primary":   "#cdd6f4",
        "text_secondary": "#6c7086",
        "border":         "#383850",
        "white":          "#ffffff",
    },
    LIGHT: {
        "bg_primary":     "#f8f8f2",
        "bg_secondary":   "#ffffff",
        "bg_tertiary":    "#efefef",
        "accent":         "#7c6af7",
        "accent_hover":   "#6c5ce7",
        "success":        "#3d8b3d",
        "error":          "#c0392b",
        "text_primary":   "#383a42",
        "text_secondary": "#9a9b9c",
        "border":         "#d0d0d0",
        "white":          "#ffffff",
    },
}

# ──────────────────────────────────────────────────────────────────────
# Template QSS
# Nota : {{ et }} = accolades littérales dans la f-string / format()
# ──────────────────────────────────────────────────────────────────────

_QSS = """

/* ── 1. Base ─────────────────────────────────────────────────────── */

QMainWindow, QDialog, QWidget {{
    background-color: {bg_primary};
    color: {text_primary};
    font-family: "Noto Sans", "Inter", "Segoe UI", sans-serif;
}}


/* ── 2. Zones de texte ───────────────────────────────────────────── */

QTextEdit {{
    background-color: {bg_secondary};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 10px;
    font-size: 14px;
    selection-background-color: {accent};
    selection-color: {white};
}}

QTextEdit:focus {{
    border: 2px solid {accent};
}}


/* ── 3. Toolbar ──────────────────────────────────────────────────── */

QToolBar {{
    background-color: {bg_tertiary};
    border: none;
    border-bottom: 1px solid {border};
    padding: 4px 10px;
    spacing: 8px;
    min-height: 46px;
}}

QToolBar::separator {{
    background-color: {border};
    width: 1px;
    margin: 6px 4px;
}}

QToolBar QLabel {{
    color: {text_primary};
    font-size: 12px;
    background: transparent;
}}

QToolButton {{
    background-color: transparent;
    color: {text_primary};
    border: none;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
}}

QToolButton:hover {{
    background-color: {bg_primary};
    color: {accent};
}}

QToolButton:pressed {{
    background-color: {border};
}}


/* ── 4. Bouton principal Traduire (#translateBtn) ─────────────────── */

QPushButton#translateBtn {{
    background-color: {accent};
    color: {white};
    font-weight: bold;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 24px;
    border: none;
}}

QPushButton#translateBtn:hover {{
    background-color: {accent_hover};
}}

QPushButton#translateBtn:pressed {{
    background-color: {accent_hover};
    padding-top: 10px;
    padding-bottom: 8px;
}}

QPushButton#translateBtn:disabled {{
    background-color: {bg_tertiary};
    color: {text_secondary};
}}


/* ── 5 & 6. Boutons secondaires (Copier, Effacer, Exporter,
              Écouter, Fichier et tous les autres) ─────────────────── */

QPushButton {{
    background-color: transparent;
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 12px;
}}

QPushButton:hover {{
    border-color: {accent};
    color: {accent};
}}

QPushButton:pressed {{
    background-color: {bg_tertiary};
}}

QPushButton:disabled {{
    color: {text_secondary};
    border-color: {border};
}}


/* ── 7. ComboBox (sélecteur moteur) ──────────────────────────────── */

QComboBox {{
    background-color: {bg_tertiary};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    min-height: 26px;
}}

QComboBox:hover {{
    border-color: {accent};
}}

QComboBox:focus {{
    border-color: {accent};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
    border-left: 2px solid {text_secondary};
    border-bottom: 2px solid {text_secondary};
    margin-right: 6px;
    /* Simulé par rotation — Qt ne supporte pas directement un ▾ QSS */
}}

QComboBox QAbstractItemView {{
    background-color: {bg_tertiary};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 4px;
    selection-background-color: {accent};
    selection-color: {white};
    outline: none;
    padding: 2px;
}}

QComboBox QAbstractItemView::item {{
    padding: 5px 10px;
    min-height: 24px;
}}

QComboBox QAbstractItemView::item:disabled {{
    color: {text_secondary};
}}


/* ── 8. StatusBar ────────────────────────────────────────────────── */

QStatusBar {{
    background-color: {bg_tertiary};
    color: {text_secondary};
    font-size: 11px;
    border-top: 1px solid {border};
}}

QStatusBar QLabel {{
    color: {text_secondary};
    font-size: 11px;
    background: transparent;
    padding: 0 2px;
}}


/* ── 9. Labels généraux ──────────────────────────────────────────── */

QLabel {{
    color: {text_secondary};
    font-size: 11px;
    background: transparent;
}}


/* ── 10. QSplitter ───────────────────────────────────────────────── */

QSplitter::handle {{
    background-color: {border};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QSplitter::handle:hover {{
    background-color: {accent};
}}


/* ── 11. Scrollbars ──────────────────────────────────────────────── */

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {accent};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: transparent;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {border};
    border-radius: 4px;
    min-width: 24px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {accent};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: transparent;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}


/* ── 12. Menu ────────────────────────────────────────────────────── */

QMenuBar {{
    background-color: {bg_tertiary};
    color: {text_primary};
    border-bottom: 1px solid {border};
    padding: 2px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {accent};
    color: {white};
}}

QMenu {{
    background-color: {bg_tertiary};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 20px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {accent};
    color: {white};
}}

QMenu::separator {{
    height: 1px;
    background: {border};
    margin: 4px 8px;
}}

QMenu::item:disabled {{
    color: {text_secondary};
    font-style: italic;
}}


/* ── 13. Compteur de caractères (QLabel inline, renforcé par QSS) ── */
/* Le style inline de text_panel.py prend la main sur la couleur
   dynamique (gris/orange/rouge). Ce sélecteur couvre le cas statique. */

QLabel[objectName="charCounter"] {{
    color: {text_secondary};
    font-size: 11px;
}}


/* ── Bouton swap ⇄ (centré sur le séparateur) ────────────────────── */

QPushButton#swapBtn {{
    background-color: {accent};
    color: {white};
    border: none;
    border-radius: 18px;
    font-size: 16px;
    font-weight: bold;
    padding: 0px;
    min-width: 36px;
    max-width: 36px;
    min-height: 36px;
    max-height: 36px;
}}

QPushButton#swapBtn:hover {{
    background-color: {accent_hover};
}}

QPushButton#swapBtn:pressed {{
    background-color: {accent_hover};
    padding-top: 1px;
}}


/* ── Extras : ProgressBar, GroupBox, inputs ──────────────────────── */

QProgressBar {{
    background-color: {bg_secondary};
    border: none;
    border-radius: 3px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 3px;
}}

QGroupBox {{
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 12px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {text_primary};
    left: 10px;
}}

QLineEdit {{
    background-color: {bg_secondary};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
    selection-background-color: {accent};
}}

QLineEdit:focus {{
    border-color: {accent};
}}

QSpinBox {{
    background-color: {bg_secondary};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}}

QSpinBox:focus {{
    border-color: {accent};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {bg_tertiary};
    border: none;
    width: 16px;
    border-radius: 3px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {accent};
}}

QCheckBox {{
    color: {text_primary};
    spacing: 8px;
    font-size: 12px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border};
    border-radius: 3px;
    background-color: {bg_secondary};
}}

QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

QCheckBox::indicator:hover {{
    border-color: {accent};
}}

/* Table historique */

QTableWidget {{
    background-color: {bg_secondary};
    color: {text_primary};
    gridline-color: {border};
    border: 1px solid {border};
    border-radius: 4px;
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 5px 8px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {accent};
    color: {white};
}}

QTableWidget::item:alternate {{
    background-color: {bg_tertiary};
}}

QHeaderView::section {{
    background-color: {bg_tertiary};
    color: {text_secondary};
    border: none;
    border-bottom: 1px solid {border};
    border-right: 1px solid {border};
    padding: 5px 8px;
    font-weight: bold;
    font-size: 11px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* Dialogue modèle (ModelManagerDialog) */

QDialog QLabel {{
    color: {text_primary};
    font-size: 12px;
}}

"""


# ──────────────────────────────────────────────────────────────────────
# API publique
# ──────────────────────────────────────────────────────────────────────

def _build_qss(theme: str) -> str:
    p = _PALETTES.get(theme, _PALETTES[DARK])
    return _QSS.format(**p)


def apply_theme(app: QApplication, theme: str = DARK):
    """Applique le thème à l'ensemble de l'application."""
    app.setStyleSheet(_build_qss(theme))


def save_theme(theme: str):
    """Persiste le choix de thème dans QSettings."""
    QSettings("libretrador", "libretrador").setValue("ui/theme", theme)


def load_theme() -> str:
    """Charge le thème mémorisé (dark par défaut)."""
    return QSettings("libretrador", "libretrador").value("ui/theme", DARK)
