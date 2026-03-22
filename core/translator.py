"""Wrapper Argos Translate + QThread worker pour ne pas bloquer l'UI."""

import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


def is_model_installed(src: str = "en", tgt: str = "fr") -> bool:
    """Retourne True si le modèle src→tgt est installé."""
    try:
        return _get_translation_pkg(src, tgt) is not None
    except Exception as e:
        logger.error(f"Erreur vérification modèle : {e}")
        return False


def _get_translation_pkg(src: str = "en", tgt: str = "fr"):
    """Retourne le paquet de traduction src→tgt installé, ou None."""
    from argostranslate import translate
    installed = translate.get_installed_languages()
    src_lang = next((l for l in installed if l.code == src), None)
    tgt_lang = next((l for l in installed if l.code == tgt), None)
    if src_lang is None or tgt_lang is None:
        return None
    pkg = src_lang.get_translation(tgt_lang)
    if pkg is None or type(pkg).__name__ == "IdentityTranslation":
        return None
    return pkg


def get_model_version() -> str:
    """Retourne une chaîne descriptive du modèle EN→FR installé."""
    try:
        pkg = _get_translation_pkg("en", "fr")
        return "installé" if pkg else "non installé"
    except Exception:
        return "inconnu"


class TranslationWorker(QThread):
    """Worker QThread pour effectuer la traduction sans bloquer l'UI."""

    result_ready     = pyqtSignal(str)
    error_occurred   = pyqtSignal(str)
    progress_updated = pyqtSignal(int)  # 0-100

    def __init__(self, text: str = "", chunks: list = None,
                 src_lang: str = "en", tgt_lang: str = "fr",
                 srt_blocks: list = None):
        super().__init__()
        self.text       = text
        self.chunks     = chunks
        self.src_lang   = src_lang
        self.tgt_lang   = tgt_lang
        self.srt_blocks = srt_blocks  # list[SrtBlock] ou None
        self._pkg       = None        # initialisé dans run()

    # ------------------------------------------------------------------

    def run(self):
        try:
            self._pkg = _get_translation_pkg(self.src_lang, self.tgt_lang)
            if self._pkg is None:
                self.error_occurred.emit(
                    f"Modèle {self.src_lang}→{self.tgt_lang} non installé"
                )
                return

            if self.srt_blocks is not None:
                self._run_srt()
            elif self.chunks:
                self._run_chunks()
            else:
                self.result_ready.emit(self._translate_text(self.text))

        except Exception as e:
            logger.error(f"Erreur traduction : {e}")
            self.error_occurred.emit(str(e))

    def _translate_text(self, text: str) -> str:
        return self._pkg.translate(text)

    def _run_chunks(self):
        results = []
        total = len(self.chunks)
        for i, chunk in enumerate(self.chunks):
            results.append(self._translate_text(chunk) if chunk.strip() else "")
            self.progress_updated.emit(int((i + 1) / total * 100))
        self.result_ready.emit("\n\n".join(results))

    def _run_srt(self):
        # Argos est quasi instantané par bloc → traduction bloc par bloc,
        # pas de chunking avec séparateur (Argos traduit §§§ en "Chapitre" etc.)
        from core.srt_translator import blocks_to_srt, SrtBlock
        translated: list[SrtBlock] = []
        total = len(self.srt_blocks)

        for i, block in enumerate(self.srt_blocks):
            tgt_text = (
                self._translate_text(block.text) if block.text.strip() else block.text
            )
            translated.append(SrtBlock(
                index=block.index,
                timecode=block.timecode,
                text=tgt_text,
            ))
            self.progress_updated.emit(int((i + 1) / total * 100))

        self.result_ready.emit(blocks_to_srt(translated))
