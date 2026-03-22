"""Surveillance du presse-papier via QTimer + QApplication.clipboard()."""

import logging
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# Mots fréquents anglais pour la détection heuristique
_EN_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "what", "which",
    "who", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "not", "only",
    "same", "so", "than", "too", "very", "just", "as", "at", "by", "for",
    "from", "in", "into", "of", "on", "or", "out", "to", "up", "with",
    "about", "after", "also", "but", "if", "its", "my", "our", "their",
    "them", "then", "there", "through", "time", "up", "use", "your",
}

# Mots fréquents français — si présents en majorité, c'est pas de l'anglais
_FR_WORDS = {
    "le", "la", "les", "un", "une", "des", "est", "sont", "était", "avec",
    "pour", "dans", "sur", "par", "et", "ou", "ne", "pas", "je", "tu",
    "il", "elle", "nous", "vous", "ils", "elles", "que", "qui", "quoi",
    "ce", "cet", "cette", "ces", "mon", "ton", "son", "ma", "ta", "sa",
    "au", "du", "aux", "mais", "donc", "car", "ni", "comme",
}


def _english_ratio(text: str) -> float:
    words = [w.strip(".,!?;:\"'()[]{}") for w in text.lower().split()]
    words = [w for w in words if w]
    if not words:
        return 0.0
    en = sum(1 for w in words if w in _EN_WORDS)
    fr = sum(1 for w in words if w in _FR_WORDS)
    if fr > en:
        return 0.0
    return en / len(words)


def is_likely_english(text: str, threshold: float = 0.12) -> bool:
    """Heuristique simple : au moins `threshold` fraction de mots anglais courants."""
    if len(text.strip()) < 15:
        return False
    return _english_ratio(text) >= threshold


class ClipboardMonitor(QObject):
    """Émet `new_english_text` quand un nouveau texte anglais est détecté."""

    new_english_text = pyqtSignal(str)

    def __init__(self, poll_ms: int = 500, parent=None):
        super().__init__(parent)
        self._last_text = ""
        self._enabled = False

        self._timer = QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self._check)

    def start(self):
        if not self._enabled:
            self._enabled = True
            self._last_text = QApplication.clipboard().text()
            self._timer.start()
            logger.info("Surveillance presse-papier activée")

    def stop(self):
        if self._enabled:
            self._enabled = False
            self._timer.stop()
            logger.info("Surveillance presse-papier désactivée")

    def _check(self):
        text = QApplication.clipboard().text()
        if text and text != self._last_text:
            self._last_text = text
            if is_likely_english(text):
                logger.debug("Texte anglais détecté dans le presse-papier")
                self.new_english_text.emit(text)
