"""Fenêtre principale de LibreTrador."""

import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QToolBar, QFileDialog,
    QProgressBar, QLabel, QSystemTrayIcon, QMenu,
    QApplication, QMessageBox, QComboBox, QDialog,
)
from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSlot
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from config import APP_NAME, APP_VERSION, MAX_CHARS
from core.translator import TranslationWorker, is_model_installed, get_model_version
from core.ollama_engine import (
    OllamaWorker, OllamaAvailabilityChecker, DEFAULT_MODEL, OLLAMA_BASE_URL
)
from core.database import init_db, save_translation
from core.glossary import apply_glossary
from core.tts import speak_french, stop_speaking, is_speaking, check_piper, PIPER_BIN, PIPER_MODEL
from core.clipboard import ClipboardMonitor
from core.file_reader import read_file
from ui.widgets.text_panel import TextPanel
from ui.widgets.status_bar import AppStatusBar
from ui.history_window import HistoryWindow
from ui.settings_dialog import SettingsDialog, load_settings
from ui.help_dialog import HelpDialog
from ui.theme import apply_theme, load_theme

logger = logging.getLogger(__name__)

_ASSETS = Path(__file__).parent.parent / "assets"

ENGINE_ARGOS  = "argos"
ENGINE_OLLAMA = "ollama"
_IDX_ARGOS  = 0
_IDX_OLLAMA = 1

# Paires de langues supportées : (src_code, tgt_code, src_label, tgt_label)
_LANG_PAIRS = {
    ("en", "fr"): ("🇬🇧 Anglais (source)", "🇫🇷 Français (cible)"),
    ("fr", "en"): ("🇫🇷 Français (source)", "🇬🇧 Anglais (cible)"),
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(920, 620)
        self.resize(1100, 680)

        self._worker = None
        self._ollama_available = False
        self._settings = load_settings()
        self._qsettings = QSettings("libretrador", "libretrador")
        self._clipboard_monitor = ClipboardMonitor(parent=self)

        # Direction de traduction (persistée)
        self._src_lang = self._qsettings.value("translation/src_lang", "en")
        self._tgt_lang = self._qsettings.value("translation/tgt_lang", "fr")

        self._tts_timer = QTimer(self)
        self._tts_timer.setInterval(400)
        self._tts_timer.timeout.connect(self._poll_tts)

        init_db()
        self._setup_icon()
        self._setup_ui()
        self._setup_tray()
        self._setup_shortcuts()
        self._refresh_argos_status()
        self._check_ollama_async()

        if self._settings.get("clipboard_monitor", False):
            self._clipboard_monitor.start()
        self._clipboard_monitor.new_english_text.connect(self._on_clipboard_english)

    # ==================================================================
    # Construction UI
    # ==================================================================

    def _setup_icon(self):
        icon_path = _ASSETS / "libretrador_48.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 4, 8, 4)
        root.setSpacing(6)

        self._build_toolbar()

        # Splitter avec les deux panneaux
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        src_lbl, tgt_lbl = _LANG_PAIRS.get(
            (self._src_lang, self._tgt_lang), _LANG_PAIRS[("en", "fr")]
        )
        self._src = TextPanel(src_lbl, readonly=False, lang=self._src_lang)
        self._tgt = TextPanel(tgt_lbl, readonly=True,  lang=self._tgt_lang)
        self._splitter.addWidget(self._src)
        self._splitter.addWidget(self._tgt)
        self._splitter.setSizes([500, 500])
        root.addWidget(self._splitter)

        # Bouton swap ⇄ (flottant, positionné sur le handle du splitter)
        self._swap_btn = QPushButton("⇄", central)
        self._swap_btn.setObjectName("swapBtn")
        self._swap_btn.setToolTip("Inverser la direction (EN↔FR)")
        self._swap_btn.clicked.connect(self._swap_languages)
        self._swap_btn.raise_()

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setMaximumHeight(6)
        self._progress.setVisible(False)
        root.addWidget(self._progress)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self._file_btn = QPushButton("📂 Fichier")
        self._file_btn.setToolTip("Ouvrir un fichier .txt, .docx ou .pdf")
        self._file_btn.clicked.connect(self._open_file)
        action_bar.addWidget(self._file_btn)

        action_bar.addStretch()

        self._translate_btn = QPushButton("🔄 Traduire")
        self._translate_btn.setObjectName("translateBtn")
        self._translate_btn.setMinimumWidth(130)
        self._translate_btn.setToolTip("Ctrl+Entrée")
        self._translate_btn.clicked.connect(self._translate)
        action_bar.addWidget(self._translate_btn)

        self._clear_btn = QPushButton("✖ Tout effacer")
        self._clear_btn.setToolTip("Effacer les deux panneaux (Ctrl+L)")
        self._clear_btn.clicked.connect(self._clear)
        action_bar.addWidget(self._clear_btn)

        self._export_btn = QPushButton("💾 Exporter")
        self._export_btn.clicked.connect(self._export)
        action_bar.addWidget(self._export_btn)

        root.addLayout(action_bar)

        self._status_bar = AppStatusBar()
        self.setStatusBar(self._status_bar)

        self._tgt.copy_requested.connect(self._copy_result)
        self._tgt.listen_requested.connect(self._toggle_tts)
        self._src.clear_requested.connect(self._on_src_cleared)
        self._tgt.clear_requested.connect(self._on_tgt_cleared)

    def _build_toolbar(self):
        tb = QToolBar("Outils")
        tb.setMovable(False)
        self.addToolBar(tb)

        config_act = QAction("⚙ Config", self)
        config_act.setToolTip("Préférences (F2)")
        config_act.triggered.connect(self._open_settings)
        tb.addAction(config_act)

        hist_act = QAction("📋 Historique", self)
        hist_act.setToolTip("Ctrl+H")
        hist_act.triggered.connect(self._open_history)
        tb.addAction(hist_act)

        help_act = QAction("❓ Aide", self)
        help_act.setToolTip("Aide (F1)")
        help_act.triggered.connect(self._open_help)
        tb.addAction(help_act)

        glossary_act = QAction("📖 Glossaire", self)
        glossary_act.setToolTip("Gérer le glossaire personnalisé (Find & Replace)")
        glossary_act.triggered.connect(self._open_glossary)
        tb.addAction(glossary_act)

        tb.addSeparator()

        title = QLabel(f"  {APP_NAME}  ")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        tb.addWidget(title)

        tb.addSeparator()

        engine_label = QLabel("  Moteur : ")
        engine_label.setStyleSheet("font-size: 11px;")
        tb.addWidget(engine_label)

        self._engine_combo = QComboBox()
        self._engine_combo.setMinimumWidth(240)
        self._engine_combo.addItem(self._argos_label())    # index 0
        self._engine_combo.addItem("🧠 Ollama (qualité, textes longs)")  # index 1
        self._engine_combo.setItemData(_IDX_OLLAMA, False, Qt.ItemDataRole.UserRole)
        self._engine_combo.model().item(_IDX_OLLAMA).setEnabled(False)
        self._engine_combo.model().item(_IDX_OLLAMA).setToolTip(
            f"Ollama non détecté sur {OLLAMA_BASE_URL}"
        )
        self._engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        tb.addWidget(self._engine_combo)

        # Restaurer le choix mémorisé
        saved = self._qsettings.value("engine/selected", ENGINE_ARGOS)
        self._pending_engine = saved  # appliqué après _check_ollama_async

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        icon_path = _ASSETS / "libretrador_48.png"
        if icon_path.exists():
            self._tray.setIcon(QIcon(str(icon_path)))
        else:
            self._tray.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))

        menu = QMenu()
        quit_act = QAction("Quitter LibreTrador", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_act)

        self._tray.setContextMenu(menu)
        self._tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _setup_shortcuts(self):
        for key, slot in [
            ("Ctrl+Return",  self._translate),
            ("Ctrl+Shift+C", self._copy_result),
            ("Ctrl+L",       self._clear),
            ("Ctrl+H",       self._open_history),
            ("F1",           self._open_help),
            ("F2",           self._open_settings),
        ]:
            act = QAction(self)
            act.setShortcut(QKeySequence(key))
            act.triggered.connect(slot)
            self.addAction(act)

    # ==================================================================
    # Direction de traduction
    # ==================================================================

    def _direction_label(self) -> str:
        return f"{self._src_lang.upper()}→{self._tgt_lang.upper()}"

    def _argos_label(self) -> str:
        return f"⚡ Argos {self._direction_label()} (rapide, < 500 car.)"

    @pyqtSlot()
    def _swap_languages(self):
        """Inverse la direction de traduction et échange le contenu des panneaux."""
        # Échanger les langues
        self._src_lang, self._tgt_lang = self._tgt_lang, self._src_lang
        self._qsettings.setValue("translation/src_lang", self._src_lang)
        self._qsettings.setValue("translation/tgt_lang", self._tgt_lang)

        # Échanger le contenu des panneaux
        src_text = self._src.get_text()
        tgt_text = self._tgt.get_text()
        self._src.set_text(tgt_text)
        self._tgt.set_text(src_text)

        self._update_direction_ui()

    def _update_direction_ui(self):
        """Met à jour tous les éléments visuels liés à la direction de traduction."""
        src_lbl, tgt_lbl = _LANG_PAIRS.get(
            (self._src_lang, self._tgt_lang), _LANG_PAIRS[("en", "fr")]
        )
        self._src.set_title(src_lbl)
        self._tgt.set_title(tgt_lbl)

        # Langue pour la recherche de synonymes
        self._src.set_lang(self._src_lang)
        self._tgt.set_lang(self._tgt_lang)

        # Placeholder texte source
        if self._src_lang == "en":
            self._src.set_placeholder("Saisissez du texte anglais ici…")
        else:
            self._src.set_placeholder("Saisissez du texte français ici…")

        # Label Argos dans le combo
        self._engine_combo.setItemText(_IDX_ARGOS, self._argos_label())

        # Barre de statut
        engine = "Ollama" if self._current_engine() == ENGINE_OLLAMA else "Argos"
        ready = is_model_installed(self._src_lang, self._tgt_lang)
        self._status_bar.set_engine_ready(ready, engine, self._direction_label())
        self._translate_btn.setEnabled(ready)

        if not ready:
            self._offer_model_download()

    def _offer_model_download(self):
        """Propose le téléchargement du modèle pour la direction courante."""
        direction = self._direction_label()
        reply = QMessageBox.question(
            self,
            "Modèle manquant",
            f"Le modèle Argos {direction} n'est pas installé.\n"
            "Voulez-vous le télécharger maintenant ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from ui.model_manager import ModelManagerDialog
            if self._src_lang == "fr":
                dlg = ModelManagerDialog(
                    src_code="fr", tgt_code="en",
                    src_name="Français", tgt_name="Anglais",
                    parent=self,
                )
            else:
                dlg = ModelManagerDialog(
                    src_code="en", tgt_code="fr",
                    src_name="Anglais", tgt_name="Français",
                    parent=self,
                )
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._refresh_argos_status()

    # ==================================================================
    # Resize — repositionnement du bouton swap
    # ==================================================================

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_swap_btn()

    def showEvent(self, event):
        super().showEvent(event)
        self._reposition_swap_btn()

    def _reposition_swap_btn(self):
        """Centre le bouton ⇄ sur la poignée du QSplitter."""
        if not hasattr(self, "_swap_btn") or not hasattr(self, "_splitter"):
            return
        # Position du handle dans les coordonnées du widget central
        handle = self._splitter.handle(1)
        if handle is None:
            return
        central = self.centralWidget()
        handle_pos = handle.mapTo(central, handle.rect().topLeft())
        btn_size = 36
        x = handle_pos.x() + (handle.width() - btn_size) // 2
        y = handle_pos.y() + (handle.height() - btn_size) // 2
        self._swap_btn.setGeometry(x, y, btn_size, btn_size)
        self._swap_btn.raise_()

    # ==================================================================
    # Statut moteurs
    # ==================================================================

    def _refresh_argos_status(self):
        ready = is_model_installed(self._src_lang, self._tgt_lang)
        engine = "Ollama" if self._current_engine() == ENGINE_OLLAMA else "Argos"
        self._status_bar.set_engine_ready(ready, engine, self._direction_label())
        if ready and self._src_lang == "en" and self._tgt_lang == "fr":
            self._status_bar.set_model_version(get_model_version())
        self._translate_btn.setEnabled(ready)
        # Vérification Piper TTS (non bloquante — juste un log + statut)
        piper_ok, piper_err = check_piper()
        if not piper_ok:
            logger.warning(f"Piper TTS : {piper_err}")
            self._tgt.set_listen_enabled(False)
            self._status_bar.set_status(f"TTS indisponible : {piper_err}", timeout=6000)

    def _check_ollama_async(self):
        """Lance la vérification de disponibilité d'Ollama en arrière-plan."""
        checker = OllamaAvailabilityChecker(self)
        checker.result.connect(self._on_ollama_status)
        checker.start()

    @pyqtSlot(bool)
    def _on_ollama_status(self, available: bool):
        self._ollama_available = available
        item = self._engine_combo.model().item(_IDX_OLLAMA)
        model_name = self._settings.get("ollama_model", DEFAULT_MODEL)

        if available:
            item.setEnabled(True)
            item.setText(f"🧠 Ollama : {model_name}")
            item.setToolTip(f"Modèle : {model_name}  —  {OLLAMA_BASE_URL}")
            self._status_bar.set_status("Ollama détecté", timeout=3000)
            # Restaurer le choix mémorisé maintenant qu'Ollama est disponible
            if getattr(self, "_pending_engine", ENGINE_ARGOS) == ENGINE_OLLAMA:
                self._engine_combo.setCurrentIndex(_IDX_OLLAMA)
        else:
            item.setEnabled(False)
            item.setText("🧠 Ollama (non disponible)")
            item.setToolTip(f"Ollama non détecté sur {OLLAMA_BASE_URL}")
            # Forcer Argos si Ollama était sélectionné
            if self._engine_combo.currentIndex() == _IDX_OLLAMA:
                self._engine_combo.setCurrentIndex(_IDX_ARGOS)

        self._pending_engine = None

    def _current_engine(self) -> str:
        return ENGINE_OLLAMA if self._engine_combo.currentIndex() == _IDX_OLLAMA else ENGINE_ARGOS

    @pyqtSlot(int)
    def _on_engine_changed(self, index: int):
        engine = ENGINE_OLLAMA if index == _IDX_OLLAMA else ENGINE_ARGOS
        self._qsettings.setValue("engine/selected", engine)
        model = self._settings.get("ollama_model", DEFAULT_MODEL)
        if engine == ENGINE_OLLAMA:
            self._status_bar.set_status(f"Moteur : Ollama ({model})", timeout=2000)
        else:
            self._status_bar.set_status(
                f"Moteur : Argos {self._direction_label()}", timeout=2000
            )

    # ==================================================================
    # Traduction texte
    # ==================================================================

    @pyqtSlot()
    def _translate(self):
        if self._worker and self._worker.isRunning():
            return

        text = self._src.get_text().strip()
        if not text:
            self._status_bar.set_status("Aucun texte à traduire")
            return
        if len(text) > MAX_CHARS and self._current_engine() == ENGINE_ARGOS:
            self._status_bar.set_status(
                f"Texte trop long pour Argos : {len(text)} / {MAX_CHARS} car. "
                "— Utilisez le moteur Ollama pour les textes longs."
            )
            return

        self._set_translating(True)
        self._tgt.reset_border()
        self._worker = self._make_worker(text)
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _make_worker(self, text: str = "", chunks: list = None):
        """Crée le worker approprié selon le moteur et la direction sélectionnés."""
        if self._current_engine() == ENGINE_OLLAMA:
            model = self._settings.get("ollama_model", DEFAULT_MODEL)
            return OllamaWorker(
                text, chunks=chunks, model=model,
                src_lang=self._src_lang, tgt_lang=self._tgt_lang,
            )
        return TranslationWorker(
            text, chunks=chunks,
            src_lang=self._src_lang, tgt_lang=self._tgt_lang,
        )

    @pyqtSlot(str)
    def _on_result(self, result: str):
        result = apply_glossary(result, self._src_lang, self._tgt_lang)
        self._tgt.set_text(result)
        self._tgt.set_border_success(True)
        self._set_translating(False)
        engine = "Ollama" if self._current_engine() == ENGINE_OLLAMA else "Argos"
        self._status_bar.set_status(f"Traduction terminée ({engine} {self._direction_label()})")
        try:
            save_translation(
                self._src.get_text().strip(), result,
                src_lang=self._src_lang, tgt_lang=self._tgt_lang,
            )
        except Exception as e:
            logger.error(f"Sauvegarde historique : {e}")

    @pyqtSlot(str)
    def _on_error(self, error: str):
        self._tgt.set_border_success(False)
        self._set_translating(False)
        self._progress.setVisible(False)
        self._status_bar.set_status(f"Erreur : {error}")
        logger.error(f"Erreur traduction : {error}")

    def _set_translating(self, active: bool):
        self._translate_btn.setEnabled(not active)
        self._translate_btn.setText("⏳ Traduction…" if active else "🔄 Traduire")

    # ==================================================================
    # Traduction fichier
    # ==================================================================

    @pyqtSlot()
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un fichier à traduire",
            str(Path.home()),
            "Fichiers supportés (*.txt *.docx *.pdf *.srt);;"
            "Sous-titres SRT (*.srt);;"
            "Fichiers texte (*.txt);;"
            "Fichiers Word (*.docx);;"
            "PDF (*.pdf);;"
            "Tous les fichiers (*)",
        )
        if not path:
            return

        filepath = Path(path)
        if filepath.suffix.lower() == ".srt":
            self._handle_srt_file(filepath)
        else:
            self._handle_text_file(filepath)

    def _handle_text_file(self, filepath: Path):
        try:
            chunks = read_file(filepath)
        except Exception as e:
            self._status_bar.set_status(f"Erreur lecture : {e}")
            return

        if not chunks:
            self._status_bar.set_status("Fichier vide ou non lisible")
            return

        preview = "\n\n".join(chunks[:3])
        if len(chunks) > 3:
            preview += f"\n\n[… {len(chunks) - 3} paragraphes supplémentaires]"
        self._src.set_text(preview)

        self._set_translating(True)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        if len(chunks) > 1 and self._current_engine() == ENGINE_ARGOS and self._ollama_available:
            self._status_bar.set_status(
                "💡 Conseil : utilisez le moteur Ollama pour les fichiers longs (meilleure qualité)"
            )

        self._worker = self._make_worker(chunks=chunks)
        self._worker.result_ready.connect(self._on_file_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.progress_updated.connect(self._progress.setValue)
        self._worker.start()

    def _handle_srt_file(self, filepath: Path):
        from core.srt_translator import parse_srt, srt_preview

        # Lecture avec fallback d'encodage
        content = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                content = filepath.read_text(encoding=enc)
                if enc != "utf-8":
                    logger.warning(f"SRT lu en {enc} : {filepath.name}")
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            self._status_bar.set_status("❌ Impossible de lire le fichier SRT (encodage inconnu)")
            return

        blocks = parse_srt(content)
        if not blocks:
            self._tgt.set_text(
                "❌ Format SRT invalide : aucun bloc détecté.\n"
                "Vérifiez que le fichier est bien un sous-titre SRT standard."
            )
            self._status_bar.set_status("Fichier SRT invalide")
            return

        # Aperçu dans le panneau source
        self._src.set_text(
            f"📄 Fichier SRT : {filepath.name}\n"
            f"{len(blocks)} blocs de sous-titres détectés\n\n"
            + srt_preview(blocks, n=3)
        )

        # Suggérer Ollama pour les SRT longs
        if self._current_engine() == ENGINE_ARGOS and self._ollama_available and len(blocks) > 20:
            self._status_bar.set_status(
                "💡 Conseil : Ollama donne de meilleurs résultats pour les sous-titres longs"
            )

        self._srt_source_path = filepath  # mémorisé pour le nom de fichier cible
        self._set_translating(True)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._tgt.set_text("⏳ Traduction des sous-titres en cours…")

        self._worker = self._make_srt_worker(blocks)
        self._worker.result_ready.connect(self._on_srt_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.progress_updated.connect(self._progress.setValue)
        self._worker.start()

    def _make_srt_worker(self, srt_blocks: list):
        """Crée le worker SRT selon le moteur sélectionné."""
        if self._current_engine() == ENGINE_OLLAMA:
            model = self._settings.get("ollama_model", DEFAULT_MODEL)
            return OllamaWorker(
                srt_blocks=srt_blocks, model=model,
                src_lang=self._src_lang, tgt_lang=self._tgt_lang,
            )
        return TranslationWorker(
            srt_blocks=srt_blocks,
            src_lang=self._src_lang, tgt_lang=self._tgt_lang,
        )

    @pyqtSlot(str)
    def _on_srt_result(self, srt_content: str):
        from core.srt_translator import parse_srt, srt_preview

        self._set_translating(False)
        self._progress.setVisible(False)

        translated_blocks = parse_srt(srt_content)
        n = len(translated_blocks)
        engine = "Ollama" if self._current_engine() == ENGINE_OLLAMA else "Argos"

        # Proposer la sauvegarde
        src = getattr(self, "_srt_source_path", None)
        suggested = str(
            (src.parent / f"{src.stem}_{self._tgt_lang.upper()}{src.suffix}")
            if src else Path.home() / f"sous-titres_{self._tgt_lang.upper()}.srt"
        )
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le fichier SRT traduit",
            suggested,
            "Sous-titres SRT (*.srt)",
        )

        # Aperçu dans le panneau cible (que l'utilisateur sauvegarde ou non)
        preview_text = (
            f"✅ {n} blocs traduits ({engine} {self._direction_label()})\n\n"
            + srt_preview(translated_blocks, n=3)
        )

        if save_path:
            try:
                Path(save_path).write_text(srt_content, encoding="utf-8")
                preview_text += f"\n\n💾 Fichier sauvegardé :\n{save_path}"
                self._status_bar.set_status(f"SRT sauvegardé : {Path(save_path).name}")
            except Exception as e:
                preview_text += f"\n\n❌ Erreur de sauvegarde : {e}"
                self._status_bar.set_status(f"Erreur sauvegarde SRT : {e}")
        else:
            self._status_bar.set_status(f"SRT traduit ({n} blocs) — non sauvegardé")

        self._tgt.set_text(preview_text)
        self._tgt.set_border_success(True)

    @pyqtSlot(str)
    def _on_file_result(self, result: str):
        result = apply_glossary(result, self._src_lang, self._tgt_lang)
        self._tgt.set_text(result)
        self._tgt.set_border_success(True)
        self._set_translating(False)
        self._progress.setVisible(False)
        self._status_bar.set_status("Traduction du fichier terminée")

    # ==================================================================
    # Copier / Effacer / Exporter
    # ==================================================================

    @pyqtSlot()
    def _copy_result(self):
        text = self._tgt.get_text()
        if text:
            QApplication.clipboard().setText(text)
            self._status_bar.set_status("Résultat copié dans le presse-papier")

    @pyqtSlot()
    def _clear(self):
        """Efface les deux panneaux."""
        stop_speaking()
        self._tts_timer.stop()
        self._tgt.set_listen_active(False)
        self._src.clear()
        self._tgt.clear()
        self._tgt.reset_border()
        self._status_bar.set_status("Panneaux effacés")

    @pyqtSlot()
    def _on_src_cleared(self):
        self._status_bar.set_status("Panneau source effacé")

    @pyqtSlot()
    def _on_tgt_cleared(self):
        stop_speaking()
        self._tts_timer.stop()
        self._tgt.set_listen_active(False)
        self._status_bar.set_status("Panneau cible effacé")

    @pyqtSlot()
    def _export(self):
        text = self._tgt.get_text().strip()
        if not text:
            self._status_bar.set_status("Rien à exporter — traduisez d'abord")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la traduction",
            str(Path.home() / "traduction.txt"),
            "Texte (*.txt);;JSON (*.json)",
        )
        if not path:
            return

        try:
            p = Path(path)
            if p.suffix.lower() == ".json":
                data = {
                    "source_lang": self._src_lang,
                    "target_lang": self._tgt_lang,
                    "direction": self._direction_label(),
                    "source": self._src.get_text(),
                    "translation": text,
                    "engine": self._current_engine(),
                }
                p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            else:
                p.write_text(text, encoding="utf-8")
            self._status_bar.set_status(f"Exporté : {p.name}")
        except Exception as e:
            self._status_bar.set_status(f"Erreur export : {e}")

    # ==================================================================
    # TTS
    # ==================================================================

    @pyqtSlot()
    def _toggle_tts(self):
        if is_speaking():
            stop_speaking()
            self._tts_timer.stop()
            self._tgt.set_listen_active(False)
            return

        text = self._tgt.get_text().strip()
        if not text:
            return

        ok, err = check_piper()
        if not ok:
            QMessageBox.warning(self, "Piper TTS manquant", err)
            return

        speak_french(text)
        self._tgt.set_listen_active(True)
        self._tts_timer.start()

    def _poll_tts(self):
        if not is_speaking():
            self._tts_timer.stop()
            self._tgt.set_listen_active(False)

    # ==================================================================
    # Historique / Préférences
    # ==================================================================

    @pyqtSlot()
    def _open_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    @pyqtSlot()
    def _open_glossary(self):
        from ui.glossary_dialog import GlossaryDialog
        dlg = GlossaryDialog(self._src_lang, self._tgt_lang, parent=self)
        dlg.exec()

    @pyqtSlot()
    def _open_history(self):
        dlg = HistoryWindow(self)
        dlg.translation_selected.connect(self._load_from_history)
        dlg.exec()

    @pyqtSlot(str, str)
    def _load_from_history(self, source: str, target: str):
        self._src.set_text(source)
        self._tgt.set_text(target)
        self._tgt.set_border_success(True)

    @pyqtSlot()
    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._settings = dlg.get_settings()
            if self._settings.get("clipboard_monitor", False):
                self._clipboard_monitor.start()
            else:
                self._clipboard_monitor.stop()
            # Ré-appliquer le thème si l'utilisateur l'a changé
            apply_theme(QApplication.instance(), load_theme())
            # Relancer la vérif Ollama + mettre à jour le label du combo
            self._check_ollama_async()

    # ==================================================================
    # Presse-papier automatique
    # ==================================================================

    @pyqtSlot(str)
    def _on_clipboard_english(self, text: str):
        self._src.set_text(text)
        if self._tray.isVisible():
            self._tray.showMessage(
                APP_NAME,
                "Texte anglais détecté — cliquez sur Traduire (Ctrl+Entrée).",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

    # ==================================================================
    # Tray / fermeture
    # ==================================================================

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        stop_speaking()
        if self._tts_timer.isActive():
            self._tts_timer.stop()
        self._tray.hide()
        event.accept()
