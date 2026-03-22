# LibreTrador

**Traducteur hors-ligne Anglais ↔ Français pour Linux**

Interface graphique native (PyQt6) permettant de traduire du texte et des fichiers de l'anglais vers le français (et du français vers l'anglais), entièrement hors-ligne via [Argos Translate](https://github.com/argosopentech/argos-translate) ou [Ollama](https://ollama.com). Aucune connexion réseau requise après le premier téléchargement du modèle.

---

## Installation rapide

### Via le paquet .deb (Debian 12+ / Ubuntu 22.04+)

```bash
# Installer le paquet
sudo dpkg -i libretrador_1.0.0_amd64.deb

# Résoudre les dépendances si nécessaire
sudo apt-get install -f

# Lancer l'application
libretrador
```

Au premier lancement, un dialogue propose de télécharger le modèle Argos EN→FR (~100 Mo, stocké dans `~/.local/share/libretrador/`). Le venv Python est créé automatiquement dans `/usr/lib/libretrador/.venv/`.

---

## Fonctionnalités

- **Traduction bidirectionnelle EN↔FR** — bascule d'un clic entre Anglais→Français et Français→Anglais
- **Deux moteurs de traduction** — Argos Translate (rapide, local) et Ollama (LLM, qualité supérieure)
- **Traduction de fichiers** — `.txt`, `.docx`, `.pdf`, `.srt` (sous-titres)
- **Traduction SRT bloc par bloc** — respect de la structure temporelle des sous-titres
- **Suggestions de synonymes** — clic droit sur un mot traduit, via WordNet/NLTK
- **Synthèse vocale** — lecture du texte traduit via Piper TTS (`fr_FR-upmc-medium`)
- **Glossaire personnalisé** — règles Find & Replace appliquées en post-traduction
- **Historique SQLite** — recherche full-text, rechargement par double-clic
- **Thèmes sombre/clair** — interface adaptable
- **Surveillance du presse-papier** — détection heuristique de texte anglais à traduire
- **Export** — `.txt` ou `.json` structuré
- **Icône dans le tray système** — fermeture réduit dans la barre, pas de quitte
- **Raccourcis clavier** — traduction, copie, effacement, historique, préférences
- **Compteur de caractères** (limite 5 000)
- **Chemins XDG standard** — `~/.config/libretrador`, `~/.local/share/libretrador`

---

## Moteurs de traduction

LibreTrador propose deux moteurs sélectionnables via le menu déroulant de la barre d'outils.

### Moteur 1 — Argos Translate (rapide)

- **Usage recommandé** : textes courts (< 500 caractères), traduction instantanée
- **Modèle** : `translate-en_fr` et `translate-fr_en` (~100 Mo chacun)
- **Dépendances** : aucune connexion réseau, fonctionne hors-ligne dès le lancement
- **Qualité** : correcte pour des phrases isolées, moins bonne sur des paragraphes longs
- **Chunking SRT** : traduction bloc par bloc pour respecter la temporisation

### Moteur 2 — Ollama (qualité)

- **Usage recommandé** : textes longs, fichiers, traductions nécessitant du contexte
- **Modèle par défaut** : `qwen2.5:14b` — recommandé pour un équilibre qualité/vitesse optimal
- **Prérequis** : [Ollama](https://ollama.com) doit tourner localement sur `http://localhost:11434`
- **Qualité** : nettement supérieure à Argos sur les textes longs et les tournures idiomatiques
- **Chunking paragraphes** : séparateur `§§§` pour conserver la structure du document

```bash
# Installer Ollama (Debian/Ubuntu)
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle recommandé (~9 Go)
ollama pull qwen2.5:14b

# Lancer le serveur Ollama (si pas démarré automatiquement)
ollama serve
```

Si Ollama n'est pas détecté au démarrage, l'option est grisée dans le sélecteur.

| Critère           | Argos Translate | Ollama qwen2.5:14b |
|-------------------|-----------------|--------------------|
| Textes courts     | Idéal           | OK                 |
| Textes longs      | Limité          | Idéal              |
| Fichiers          | Lent            | Recommandé         |
| Hors-ligne        | Toujours        | Oui (modèle local) |
| Vitesse           | Très rapide     | Plus lent          |
| Qualité           | ★★★☆☆           | ★★★★★              |

---

## Dépendances système

### Requises

```bash
sudo apt install python3 python3-pyqt6 espeak-ng libespeak-ng1
```

### Optionnelles

| Fonctionnalité     | Commande d'installation                              |
|--------------------|------------------------------------------------------|
| Synthèse vocale    | Voir section Piper TTS ci-dessous                    |
| Moteur Ollama      | `curl -fsSL https://ollama.com/install.sh \| sh`     |

### Synthèse vocale — Piper TTS

La lecture audio utilise [Piper TTS](https://github.com/rhasspy/piper) et `aplay`.

```bash
# Télécharger le binaire piper
mkdir -p ~/.local/bin
wget -O /tmp/piper.tar.gz \
  https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz
tar -xzf /tmp/piper.tar.gz -C ~/.local/bin --strip-components=1

# Télécharger la voix française upmc-medium
mkdir -p ~/.local/share/piper-voices
wget -O ~/.local/share/piper-voices/fr_FR-upmc-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx
wget -O ~/.local/share/piper-voices/fr_FR-upmc-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/upmc/medium/fr_FR-upmc-medium.onnx.json
```

Si Piper n'est pas installé, le bouton **Écouter** est désactivé — l'application reste pleinement fonctionnelle.

---

## Build depuis les sources

### 1. Cloner le dépôt

```bash
git clone https://github.com/nouhailler/libretrador.git
cd libretrador
```

### 2. Setup automatique (recommandé)

```bash
./setup.sh
```

Ce script crée un virtualenv dans `.venv/` et installe toutes les dépendances Python (`PyQt6`, `argostranslate`, `python-docx`, `pypdf`, `nltk`, `piper-tts`, etc.).

### 3. Lancement en développement

```bash
./run.sh
```

Ou manuellement :

```bash
source .venv/bin/activate
python3 main.py
```

### 4. Build du paquet Debian

```bash
./build_deb.sh
# ou
dpkg-deb --build --root-owner-group pkg/libretrador_1.0.0_amd64/ libretrador_1.0.0_amd64.deb
```

> **Debian 12+ / externally-managed-environment** : N'utilisez pas `pip install` directement — passez toujours par le venv via `setup.sh`.

---

## Raccourcis clavier

| Raccourci        | Action                    |
|------------------|---------------------------|
| `Ctrl+Entrée`    | Lancer la traduction      |
| `Ctrl+Shift+C`   | Copier le résultat        |
| `Ctrl+L`         | Effacer les deux zones    |
| `Ctrl+H`         | Ouvrir l'historique       |
| `F2`             | Ouvrir les préférences    |

---

## Stack technique

| Composant       | Bibliothèque / Outil          |
|-----------------|-------------------------------|
| GUI             | PyQt6                         |
| Traduction      | argostranslate / Ollama API   |
| Synonymes       | NLTK WordNet                  |
| Synthèse vocale | Piper TTS + aplay             |
| Base de données | sqlite3 (stdlib)              |
| Lecture .docx   | python-docx                   |
| Lecture .pdf    | pypdf                         |
| Lecture .srt    | parser interne (regex)        |
| Presse-papier   | QApplication.clipboard()     |

---

## Note Wayland

Le tray icon peut être instable sur certains compositeurs Wayland.
En cas de problème, lancer avec :

```bash
QT_QPA_PLATFORM=xcb python3 main.py
```

---

## Licence

MIT
