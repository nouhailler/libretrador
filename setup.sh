#!/bin/bash
# setup.sh — Crée le venv et installe les dépendances de LibreTrador
# argostranslate est installé --no-deps pour éviter stanza/spacy/torch/CUDA.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"
PIP="$VENV/bin/pip"

echo "=== LibreTrador — Installation ==="

# ── 1. Dépendances système ────────────────────────────────────────────
echo ""
echo "→ Vérification des dépendances système…"
MISSING=()
command -v espeak-ng &>/dev/null || MISSING+=("espeak-ng")
python3 -c "import venv" 2>/dev/null || MISSING+=("python3-full")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "  ✗ Paquets système manquants : ${MISSING[*]}"
    echo "    Installez-les avec :"
    echo "      sudo apt install ${MISSING[*]}"
    exit 1
fi
echo "  ✓ OK"

# ── 2. Virtualenv ─────────────────────────────────────────────────────
echo ""
if [ ! -d "$VENV" ]; then
    echo "→ Création du virtualenv dans .venv/ …"
    python3 -m venv "$VENV"
else
    echo "→ Virtualenv existant trouvé (.venv/)"
fi

"$PIP" install --upgrade pip --quiet

# Chemin site-packages réel (python3.X)
SITE=$("$VENV/bin/python3" -c "import site; print(site.getsitepackages()[0])")

# ── 3. Stub stanza ────────────────────────────────────────────────────
# argostranslate/sbd.py fait « import stanza » en haut de fichier.
# Ce stub satisfait l'import sans charger PyTorch ni CUDA.
echo ""
echo "→ Création du stub stanza (évite PyTorch/CUDA)…"
mkdir -p "$SITE/stanza"
cat > "$SITE/stanza/__init__.py" << 'STUB'
"""
Stub stanza minimal pour LibreTrador.
argostranslate/sbd.py importe stanza au niveau module ; ce stub
satisfait l'import. Pipeline() ne sera jamais appelé car translate.py
est patché pour utiliser MiniSBDSentencizer à la place.
"""

class Document:
    def __init__(self):
        self.sentences = []

class Pipeline:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("stanza non installé — le patch translate.py devrait empêcher cet appel")
    def __call__(self, *args, **kwargs):
        raise RuntimeError("stanza.Pipeline non disponible")

def download(*args, **kwargs):
    raise RuntimeError("stanza.download non disponible")
STUB
echo "  ✓ OK"

# ── 4. Dépendances runtime d'argostranslate ───────────────────────────
echo ""
echo "→ Installation des dépendances d'argostranslate (sans PyTorch/CUDA)…"
"$PIP" install \
    "ctranslate2>=4.0,<5" \
    "sentencepiece>=0.2.0,<0.3" \
    "sacremoses>=0.0.53,<0.2" \
    "minisbd" \
    "packaging"
echo "  ✓ OK"

# ── 5. argostranslate --no-deps ───────────────────────────────────────
echo ""
echo "→ Installation d'argostranslate (sans dépendances déclarées)…"
"$PIP" install --no-deps "argostranslate==1.11.0"
echo "  ✓ OK"

# ── 6. Patch translate.py : StanzaSentencizer → MiniSBDSentencizer ────
# Le paquet translate-en_fr contient un dossier stanza/ → argostranslate
# sélectionne StanzaSentencizer. On redirige vers MiniSBDSentencizer.
echo ""
echo "→ Patch argostranslate/translate.py (force MiniSBD au lieu de Stanza)…"
TRANSLATE_PY="$SITE/argostranslate/translate.py"
if grep -q 'Sentencizer = StanzaSentencizer' "$TRANSLATE_PY"; then
    sed -i 's/Sentencizer = StanzaSentencizer$/Sentencizer = MiniSBDSentencizer  # patché: stanza non installé/' \
        "$TRANSLATE_PY"
    echo "  ✓ OK (lignes patchées : $(grep -c 'patché' "$TRANSLATE_PY"))"
else
    echo "  ✓ Déjà patché ou pattern introuvable — aucun changement"
fi

# ── 7. PyQt6 et lecteurs de fichiers ──────────────────────────────────
echo ""
echo "→ Installation de PyQt6, python-docx, pypdf…"
"$PIP" install "PyQt6>=6.5.0" "python-docx>=1.1.0" "pypdf>=4.0.0"
echo "  ✓ OK"

# ── 8. NLTK + données WordNet (synonymes) ─────────────────────────────
echo ""
echo "→ Installation de NLTK…"
"$PIP" install "nltk>=3.8"
echo "→ Téléchargement des corpus WordNet (synonymes EN et FR)…"
"$VENV/bin/python3" -c "
import nltk, sys
# Répertoire dans le venv pour éviter d'écrire dans ~/
import os
nltk_data = os.path.join('$VENV', 'nltk_data')
os.makedirs(nltk_data, exist_ok=True)
nltk.data.path.insert(0, nltk_data)
for pkg in ('wordnet', 'omw-1.4'):
    nltk.download(pkg, download_dir=nltk_data, quiet=True)
    print(f'  ✓ {pkg}')
"
echo "  ✓ OK"

# ── Vérification finale ───────────────────────────────────────────────
echo ""
echo "→ Vérification de la traduction…"
"$VENV/bin/python3" - << 'PYCHECK'
from argostranslate import translate
langs = translate.get_installed_languages()
codes = {l.code for l in langs}
assert "en" in codes and "fr" in codes, f"Langues installées : {codes}"
en = next(l for l in langs if l.code == "en")
fr = next(l for l in langs if l.code == "fr")
result = en.get_translation(fr).translate("Hello world")
assert result, "Traduction vide"
print(f'  ✓ Test OK : "Hello world" → "{result}"')
PYCHECK

# ── Résumé ────────────────────────────────────────────────────────────
echo ""
echo "=== Installation terminée ==="
VENV_SIZE=$(du -sh "$VENV" 2>/dev/null | cut -f1)
echo "  Taille du venv : ${VENV_SIZE}"
echo ""
echo "Pour lancer LibreTrador :"
echo "    ./run.sh"
