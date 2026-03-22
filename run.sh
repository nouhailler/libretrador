#!/bin/bash
# run.sh — Lance LibreTrador depuis le venv
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"

if [ ! -d "$VENV" ]; then
    echo "Virtualenv non trouvé. Lancez d'abord : ./setup.sh"
    exit 1
fi

# Rendre les données NLTK du venv visibles (synonymes WordNet)
export NLTK_DATA="$VENV/nltk_data:${NLTK_DATA:-}"

exec "$VENV/bin/python3" "$DIR/main.py" "$@"
