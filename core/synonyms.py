"""Recherche de synonymes via NLTK WordNet (EN et FR)."""

import logging

logger = logging.getLogger(__name__)

# Correspondance code ISO 639-1 → code langue WordNet / OMW
_LANG_MAP = {
    "en": "eng",
    "fr": "fra",
}


def get_synonyms(word: str, lang: str = "en") -> list[str]:
    """
    Retourne jusqu'à 10 synonymes pour un mot donné.

    lang : 'en' (anglais) ou 'fr' (français)
    Retourne [] silencieusement si WordNet n'est pas disponible
    ou si aucun synonyme n'est trouvé.
    """
    try:
        from nltk.corpus import wordnet as wn
        nltk_lang = _LANG_MAP.get(lang, "eng")
        synsets = wn.synsets(word, lang=nltk_lang)
        synonymes: set[str] = set()
        for syn in synsets[:4]:
            for lemma in syn.lemmas(nltk_lang):
                candidate = lemma.name().replace("_", " ")
                if candidate.lower() != word.lower():
                    synonymes.add(candidate)
        return sorted(synonymes)[:10]
    except Exception:
        # WordNet non téléchargé, NLTK absent, ou mot inconnu → silencieux
        return []
