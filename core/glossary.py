"""Glossaire personnalisé — règles de remplacement post-traduction.

Format d'une règle (dict) :
  {
    "term":           str   — texte à rechercher dans la traduction,
    "replacement":    str   — texte de remplacement,
    "enabled":        bool  — règle active ou non (défaut : True),
    "case_sensitive": bool  — correspondance sensible à la casse (défaut : False),
    "whole_word":     bool  — correspondance mot entier seulement (défaut : True)
  }
"""

import json
import re
import logging
from pathlib import Path

from config import CONFIG_DIR

logger = logging.getLogger(__name__)


def _path(src_lang: str, tgt_lang: str) -> Path:
    return CONFIG_DIR / f"glossary_{src_lang}_{tgt_lang}.json"


def load_glossary(src_lang: str = "en", tgt_lang: str = "fr") -> list[dict]:
    """Retourne la liste des règles pour la direction src→tgt."""
    p = _path(src_lang, tgt_lang)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception as e:
            logger.warning(f"Glossaire {src_lang}→{tgt_lang} illisible : {e}")
    return []


def save_glossary(rules: list[dict], src_lang: str = "en", tgt_lang: str = "fr"):
    """Persiste les règles dans ~/.config/libretrador/glossary_<src>_<tgt>.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _path(src_lang, tgt_lang).write_text(
        json.dumps(rules, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def apply_glossary(text: str, src_lang: str = "en", tgt_lang: str = "fr") -> str:
    """Applique les règles actives du glossaire au texte traduit.

    Les règles sont appliquées dans l'ordre de la liste.
    """
    rules = load_glossary(src_lang, tgt_lang)
    if not rules:
        return text

    for rule in rules:
        if not rule.get("enabled", True):
            continue
        term = rule.get("term", "").strip()
        replacement = rule.get("replacement", "")
        if not term:
            continue

        flags = 0 if rule.get("case_sensitive", False) else re.IGNORECASE
        pattern = re.escape(term)
        if rule.get("whole_word", True):
            pattern = rf"\b{pattern}\b"

        try:
            text = re.sub(pattern, replacement, text, flags=flags)
        except re.error as e:
            logger.warning(f"Règle glossaire invalide '{term}' : {e}")

    return text


def glossary_path(src_lang: str = "en", tgt_lang: str = "fr") -> Path:
    """Retourne le chemin du fichier glossaire (utile pour l'UI)."""
    return _path(src_lang, tgt_lang)
