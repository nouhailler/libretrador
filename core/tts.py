"""Synthèse vocale via Piper TTS + aplay (non bloquant — QThread)."""

import os
import logging
import subprocess
from pathlib import Path

from PyQt6.QtCore import QThread

logger = logging.getLogger(__name__)

# Chemins fixes pour Piper
_HOME       = Path.home()
PIPER_BIN   = _HOME / ".local" / "bin" / "piper"
PIPER_MODEL = _HOME / ".local" / "share" / "piper-voices" / "fr_FR-upmc-medium.onnx"

# Thread actif (un seul à la fois)
_tts_thread: "_PiperThread | None" = None


# ──────────────────────────────────────────────
# Vérification de disponibilité
# ──────────────────────────────────────────────

def check_piper() -> tuple[bool, str]:
    """
    Vérifie que le binaire piper et le modèle vocal existent.
    Retourne (True, "") ou (False, message_erreur).
    """
    if not PIPER_BIN.exists():
        return False, f"Binaire Piper introuvable : {PIPER_BIN}"
    if not PIPER_MODEL.exists():
        return False, f"Modèle vocal introuvable : {PIPER_MODEL}"
    return True, ""


# ──────────────────────────────────────────────
# Worker QThread
# ──────────────────────────────────────────────

class _PiperThread(QThread):
    """
    Lance piper + aplay en pipeline dans un thread séparé.
    piper --output_raw → stdout → aplay stdin (PCM 22050 Hz, S16_LE)
    """

    def __init__(self, text: str):
        super().__init__()
        self.text        = text
        self._proc_piper: subprocess.Popen | None = None
        self._proc_aplay: subprocess.Popen | None = None

    def run(self):
        try:
            self._proc_piper = subprocess.Popen(
                [str(PIPER_BIN), "--model", str(PIPER_MODEL), "--output_raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self._proc_aplay = subprocess.Popen(
                ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                stdin=self._proc_piper.stdout,
                stderr=subprocess.DEVNULL,
            )
            # Fermer stdout côté parent pour que aplay reçoive EOF correctement
            self._proc_piper.stdout.close()

            self._proc_piper.stdin.write(self.text.encode("utf-8"))
            self._proc_piper.stdin.close()
            self._proc_aplay.wait()

        except Exception as e:
            logger.error(f"Erreur Piper TTS : {e}")
        finally:
            self._cleanup()

    def stop(self):
        """Arrête piper et aplay proprement."""
        self._cleanup()

    def _cleanup(self):
        for proc in (self._proc_aplay, self._proc_piper):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=1)
                except Exception:
                    proc.kill()


# ──────────────────────────────────────────────
# API publique
# ──────────────────────────────────────────────

def speak_french(text: str):
    """Lance la lecture du texte en français via Piper (non bloquant)."""
    global _tts_thread
    stop_speaking()

    ok, err = check_piper()
    if not ok:
        logger.error(err)
        return

    _tts_thread = _PiperThread(text)
    _tts_thread.start()


def stop_speaking():
    """Interrompt la lecture en cours si active."""
    global _tts_thread
    if _tts_thread and _tts_thread.isRunning():
        _tts_thread.stop()
        _tts_thread.wait(2000)
    _tts_thread = None


def is_speaking() -> bool:
    """Retourne True si une lecture Piper est en cours."""
    return _tts_thread is not None and _tts_thread.isRunning()
