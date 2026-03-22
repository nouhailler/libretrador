"""Moteur de traduction Ollama (LLM local via HTTP)."""

import json
import logging
import urllib.request
import urllib.error
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL   = "qwen2.5:14b"
REQUEST_TIMEOUT = 180  # secondes — les gros modèles sont lents

_PROMPTS = {
    ("en", "fr"): (
        "Translate the following English text to French. "
        "Output only the French translation, no explanation, "
        "no commentary, no Chinese characters."
    ),
    ("fr", "en"): (
        "Translate the following French text to English. "
        "Output only the English translation, no explanation, no commentary."
    ),
}

# Suffixe ajouté au prompt système en mode SRT (chunking §§§)
_SRT_SEPARATOR_INSTRUCTION = (
    " The separator §§§ must be kept exactly as-is between each subtitle block. "
    "Never translate, remove or replace §§§. It is a technical marker, not part of the text."
)


def is_ollama_available(timeout: int = 3) -> bool:
    """Ping Ollama sur localhost:11434 — retourne True si le serveur répond."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=timeout):
            return True
    except Exception:
        return False


def _call_ollama(text: str, model: str,
                 src_lang: str = "en", tgt_lang: str = "fr",
                 srt_mode: bool = False) -> str:
    """Appel synchrone à /api/generate (stream=false). Bloquant — à exécuter dans un QThread."""
    system = _PROMPTS.get((src_lang, tgt_lang), _PROMPTS[("en", "fr")])
    if srt_mode:
        system += _SRT_SEPARATOR_INSTRUCTION
    payload = json.dumps({
        "model": model,
        "prompt": text,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.1},  # déterministe pour la traduction
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read())
        return data["response"].strip()


class OllamaAvailabilityChecker(QThread):
    """Vérifie la disponibilité d'Ollama en arrière-plan (non bloquant)."""
    result = pyqtSignal(bool)

    def run(self):
        self.result.emit(is_ollama_available())


class OllamaWorker(QThread):
    """Worker QThread pour la traduction Ollama."""

    result_ready     = pyqtSignal(str)
    error_occurred   = pyqtSignal(str)
    progress_updated = pyqtSignal(int)  # 0-100 pour les fichiers

    def __init__(self, text: str = "", chunks: list = None, model: str = DEFAULT_MODEL,
                 src_lang: str = "en", tgt_lang: str = "fr",
                 srt_blocks: list = None):
        super().__init__()
        self.text       = text
        self.chunks     = chunks
        self.model      = model
        self.src_lang   = src_lang
        self.tgt_lang   = tgt_lang
        self.srt_blocks = srt_blocks  # list[SrtBlock] ou None

    def _translate_text(self, text: str) -> str:
        return _call_ollama(text, self.model, self.src_lang, self.tgt_lang)

    def run(self):
        try:
            if self.srt_blocks is not None:
                self._run_srt()
            elif self.chunks:
                self._run_chunks()
            else:
                self.result_ready.emit(self._translate_text(self.text))
        except urllib.error.URLError as e:
            msg = f"Ollama inaccessible ({OLLAMA_BASE_URL}) : {e.reason}"
            logger.error(msg)
            self.error_occurred.emit(msg)
        except Exception as e:
            logger.error(f"Erreur Ollama : {e}")
            self.error_occurred.emit(str(e))

    def _run_chunks(self):
        results = []
        total = len(self.chunks)
        for i, chunk in enumerate(self.chunks):
            results.append(self._translate_text(chunk) if chunk.strip() else "")
            self.progress_updated.emit(int((i + 1) / total * 100))
        self.result_ready.emit("\n\n".join(results))

    def _translate_srt_text(self, text: str) -> str:
        """Appel Ollama en mode SRT (prompt avec instruction §§§)."""
        return _call_ollama(text, self.model, self.src_lang, self.tgt_lang, srt_mode=True)

    def _run_srt(self):
        from core.srt_translator import chunk_blocks, blocks_to_srt, SrtBlock
        translated: list[SrtBlock] = []
        all_chunks = list(chunk_blocks(self.srt_blocks, max_chars=1500))
        total = len(all_chunks)

        for i, (blk_list, combined) in enumerate(all_chunks):
            expected_seps = len(blk_list) - 1  # nb de §§§ attendus dans la réponse
            translated_combined = self._translate_srt_text(combined)
            received_seps = translated_combined.count("§§§")

            if received_seps == expected_seps:
                # Cas nominal : découpage sur §§§
                parts = translated_combined.split("§§§")
                for j, block in enumerate(blk_list):
                    translated.append(SrtBlock(
                        index=block.index,
                        timecode=block.timecode,
                        text=parts[j].strip() if parts[j].strip() else block.text,
                    ))
            else:
                # Fallback : Ollama a altéré les séparateurs → bloc par bloc
                logger.warning(
                    f"Chunk SRT {i+1}/{total} : {received_seps} §§§ reçus "
                    f"(attendu {expected_seps}) — fallback bloc par bloc"
                )
                for block in blk_list:
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
