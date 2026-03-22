# 🌍 LibreTrador

> **Traducteur hors-ligne Anglais 🇬🇧 ↔ Français 🇫🇷 pour Linux**

Interface graphique native (PyQt6) pour traduire textes et fichiers entre l'anglais et le français, **entièrement hors-ligne** via [Argos Translate](https://github.com/argosopentech/argos-translate) ou [Ollama](https://ollama.com). Aucune connexion réseau requise après l'installation du modèle.

<br>

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 🔄 **Traduction bidirectionnelle** | Bascule EN 🇬🇧 → FR 🇫🇷 / FR 🇫🇷 → EN 🇬🇧 en un clic |
| ⚙️ **Deux moteurs** | Argos Translate (rapide & léger) et Ollama (LLM, haute qualité) |
| 📄 **Fichiers supportés** | `.txt`, `.docx`, `.pdf`, `.srt` (sous-titres) |
| 🎬 **Sous-titres SRT** | Traduction bloc par bloc, structure temporelle préservée |
| 📖 **Synonymes** | Clic droit sur un mot → suggestions via WordNet/NLTK |
| 🔊 **Synthèse vocale** | Lecture du texte traduit via Piper TTS (`fr_FR-upmc-medium`) |
| 📚 **Glossaire personnalisé** | Règles Find & Replace appliquées après traduction |
| 🕐 **Historique SQLite** | Recherche full-text, rechargement par double-clic |
| 🌓 **Thèmes sombre/clair** | Interface adaptable à votre environnement |
| 📋 **Surveillance presse-papier** | Détection heuristique de texte anglais à traduire |
| 💾 **Export** | `.txt` ou `.json` structuré |
| 🖥️ **Tray système** | Réduction dans la barre, pas de fermeture accidentelle |
| ⌨️ **Raccourcis clavier** | Traduction, copie, effacement, historique, préférences |
| 🔢 **Compteur de caractères** | Limite à 5 000 caractères |

<br>

---

## 🚀 Installation rapide

### Via le paquet `.deb` (Debian 12+ / Ubuntu 22.04+)

```bash
# Installer le paquet
sudo dpkg -i libretrador_1.0.0_amd64.deb

# Résoudre les dépendances si nécessaire
sudo apt-get install -f

# Lancer l'application
libretrador
```

> Au premier lancement, un dialogue propose de télécharger le modèle Argos EN 🇬🇧 → FR 🇫🇷 (~100 Mo).
> Le modèle est stocké dans `~/.local/share/libretrador/`. Le venv Python est créé automatiquement dans `/usr/lib/libretrador/.venv/`.

<br>

---

## 🔀 Direction de traduction

LibreTrador prend en charge la traduction dans les deux sens :

```
🇬🇧 Anglais  ──────⇄──────  🇫🇷 Français
```

Le bouton **⇄** au centre de l'interface permet de basculer instantanément la direction. Les zones source et cible sont échangées et la langue des panneaux, du moteur et des suggestions de synonymes s'adapte automatiquement.

<br>

---

## ⚙️ Moteurs de traduction

LibreTrador propose deux moteurs sélectionnables via le menu déroulant de la barre d'outils.

### 🟢 Argos Translate — Rapide & léger

- **Usage recommandé** : textes courts (< 500 caractères), traduction instantanée
- **Modèles** : `translate-en_fr` et `translate-fr_en` (~100 Mo chacun)
- **Hors-ligne** : fonctionne dès l'installation, aucune connexion réseau
- **SRT** : traduction bloc par bloc pour respecter la temporisation des sous-titres

### 🟣 Ollama — Haute qualité (LLM local)

- **Usage recommandé** : textes longs, fichiers, tournures idiomatiques
- **Modèle par défaut** : `qwen2.5:14b` — meilleur équilibre qualité/vitesse
- **Prérequis** : [Ollama](https://ollama.com) doit tourner sur `http://localhost:11434`
- **SRT** : chunking avec séparateur `§§§` + instruction de préservation dans le prompt système

```bash
# Installer Ollama (Debian/Ubuntu)
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle recommandé (~9 Go)
ollama pull qwen2.5:14b

# Démarrer le serveur (si non automatique)
ollama serve
```

> Si Ollama n'est pas détecté au démarrage, l'option est automatiquement grisée dans le sélecteur.

### Comparatif des moteurs

| Critère | 🟢 Argos Translate | 🟣 Ollama qwen2.5:14b |
|---|---|---|
| Textes courts 🇬🇧↔🇫🇷 | ✅ Idéal | 🟡 OK |
| Textes longs 🇬🇧↔🇫🇷 | 🟡 Limité | ✅ Idéal |
| Fichiers (`.txt`, `.docx`, `.pdf`) | 🟡 Lent | ✅ Recommandé |
| Sous-titres `.srt` 🎬 | ✅ Bloc par bloc | ✅ Chunking §§§ |
| Hors-ligne | ✅ Toujours | ✅ Modèle local |
| Vitesse | ⚡ Très rapide | 🐢 Plus lent |
| Qualité EN→FR / FR→EN | ★★★☆☆ | ★★★★★ |

<br>

---

## 📖 Glossaire personnalisé

Le glossaire permet d'appliquer des règles **Find & Replace** automatiquement après chaque traduction.

- Règles par direction (🇬🇧→🇫🇷 et 🇫🇷→🇬🇧 indépendantes)
- Options : correspondance exacte, limite de mot (`\b`), sensibilité à la casse
- Import/Export JSON
- Stocké dans `~/.config/libretrador/glossary_en_fr.json`

<br>

---

## 🎬 Traduction de sous-titres SRT

```
📂 film.srt  ──[traduction]──▶  📂 film_FR.srt
```

1. Ouvrir un fichier `.srt` via **Fichier → Ouvrir**
2. Un aperçu des 3 premiers blocs s'affiche dans le panneau source
3. Lancer la traduction (le moteur sélectionné est utilisé)
4. À la fin, une boîte de dialogue propose de sauvegarder le fichier traduit

> La structure temporelle (`00:00:01,000 --> 00:00:03,500`) est entièrement préservée.

<br>

---

## 🔊 Synthèse vocale — Piper TTS

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

> Si Piper n'est pas installé, le bouton **Écouter** est désactivé. L'application reste pleinement fonctionnelle.

<br>

---

## ⌨️ Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+Entrée` | 🔄 Lancer la traduction |
| `Ctrl+Shift+C` | 📋 Copier le résultat |
| `Ctrl+L` | 🗑️ Effacer les deux zones |
| `Ctrl+H` | 🕐 Ouvrir l'historique |
| `F2` | ⚙️ Ouvrir les préférences |

<br>

---

## 🛠️ Build depuis les sources

### 1. Cloner le dépôt

```bash
git clone https://github.com/nouhailler/libretrador.git
cd libretrador
```

### 2. Setup automatique

```bash
./setup.sh
```

Ce script crée un virtualenv dans `.venv/` et installe toutes les dépendances Python (`PyQt6`, `argostranslate`, `python-docx`, `pypdf`, `nltk`, `piper-tts`, etc.) et télécharge les données WordNet pour les synonymes.

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
dpkg-deb --build --root-owner-group pkg/libretrador_1.0.0_amd64/ libretrador_1.0.0_amd64.deb
```

> **Debian 12+ / externally-managed-environment** : N'utilisez pas `pip install` directement — passez toujours par le venv via `setup.sh`.

<br>

---

## 📦 Dépendances système

### Requises

```bash
sudo apt install python3 python3-pyqt6 espeak-ng libespeak-ng1
```

### Optionnelles

| Fonctionnalité | Commande |
|---|---|
| 🔊 Synthèse vocale | Voir section Piper TTS ci-dessus |
| 🟣 Moteur Ollama | `curl -fsSL https://ollama.com/install.sh \| sh` |

<br>

---

## 🧩 Stack technique

| Composant | Bibliothèque / Outil |
|---|---|
| 🖥️ GUI | PyQt6 |
| 🇬🇧↔🇫🇷 Traduction | argostranslate / Ollama API |
| 📖 Synonymes | NLTK WordNet |
| 🔊 Synthèse vocale | Piper TTS + aplay |
| 🗄️ Base de données | sqlite3 (stdlib) |
| 📄 Lecture `.docx` | python-docx |
| 📄 Lecture `.pdf` | pypdf |
| 🎬 Lecture `.srt` | Parser interne (regex) |
| 📋 Presse-papier | QApplication.clipboard() |

<br>

---

## 🗂️ Chemins XDG

| Données | Emplacement |
|---|---|
| Configuration & glossaire | `~/.config/libretrador/` |
| Modèles Argos & historique | `~/.local/share/libretrador/` |

<br>

---

## 🖥️ Note Wayland

Le tray icon peut être instable sur certains compositeurs Wayland.
En cas de problème, lancer avec :

```bash
QT_QPA_PLATFORM=xcb python3 main.py
```

<br>

---

## 📜 Licence

MIT — Libre d'utilisation, modification et redistribution.
