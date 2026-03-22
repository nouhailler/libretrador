# Spécifications du Projet : "LibreTrador" v2.0

---

## 1. Vue d'ensemble

- **Nom du projet** : LibreTrador
- **Objectif** : Interface graphique native Linux pour traduire du texte et des fichiers (Anglais → Français) de façon entièrement hors-ligne.
- **Système cible** : Debian 12+ (Bookworm / Trixie)
- **Langage** : Python 3.10+
- **Licence** : MIT

---

## 2. Décision architecturale : choix du moteur de traduction

> **Choix retenu : Argos Translate (lib Python directe)**

| Critère | Argos Translate | LibreTranslate |
|---|---|---|
| Intégration Python | `import argostranslate` | Appels HTTP REST |
| Dépendance serveur | Aucune | Serveur local requis |
| Offline | Oui (après téléchargement des modèles) | Oui (si self-hosted) |
| Complexité | Faible | Moyenne (gestion du process serveur) |
| Licence | MIT | AGPL-3.0 |

**Pourquoi Argos et pas LibreTranslate ?**
LibreTranslate utilise Argos en backend. Autant appeler Argos directement — on évite la couche HTTP, la gestion d'un sous-processus serveur, et les problèmes de port déjà occupé. L'API Python d'Argos est simple et stable.

**Note sur le premier lancement** : le modèle EN→FR (~100 Mo) est téléchargé au premier démarrage. L'application doit détecter son absence, proposer le téléchargement via un dialogue dédié, et refuser de démarrer sans lui.

---

## 3. Stack technique

| Composant | Bibliothèque | Notes |
|---|---|---|
| GUI | PyQt6 | Cohérent avec Dessinator/rssnews |
| Traduction | argostranslate | Pure Python, offline |
| Gestion presse-papier | `QApplication.clipboard()` | Natif PyQt6 — évite pyperclip/Wayland |
| Base de données | sqlite3 | Intégré Python, pas de dépendance |
| Synthèse vocale | subprocess + espeak-ng | Plus fiable que pyttsx3 sous Linux |
| Lecture fichiers .docx | python-docx | Optionnel selon MVP |
| Lecture fichiers .pdf | pypdf | Optionnel selon MVP |
| Icônes | Qt Awesome ou assets SVG/PNG custom | |

**Pourquoi `espeak-ng` plutôt que `pyttsx3` ?**
`pyttsx3` est mal maintenu sous Linux et ses backends (espeak, festival) produisent des voix françaises de qualité médiocre sans configuration manuelle. `espeak-ng` est disponible directement dans les dépôts Debian (`sudo apt install espeak-ng`) et s'appelle proprement en subprocess.

```python
# core/tts.py
import subprocess

def speak_french(text: str):
    subprocess.Popen(
        ["espeak-ng", "-v", "fr", "-s", "145", text],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
```

---

## 4. Spécifications fonctionnelles

### 4.1 MVP (Minimum Viable Product)

1. **Zone de saisie (Source)** : champ texte multiligne, texte en anglais
2. **Zone de résultat (Cible)** : champ texte multiligne en lecture seule, texte en français
3. **Bouton "Traduire"** : déclenche la traduction via Argos dans un `QThread`
4. **Bouton "Copier"** : copie le résultat via `QApplication.clipboard()`
5. **Bouton "Effacer"** : vide les deux zones
6. **Compteur de caractères** : affiché sous la zone source (limite indicative : 5 000 caractères)
7. **Traduction de fichiers** :
   - Formats supportés : `.txt` (MVP), `.docx` et `.pdf` (v1.1)
   - Sélection via `QFileDialog`
   - Traduction par blocs (paragraphes) avec `QProgressBar`
   - Export du résultat en `.txt`

### 4.2 Fonctionnalités avancées (post-MVP)

1. **Surveillance du presse-papier** :
   - `QTimer` interrogeant `QApplication.clipboard()` toutes les 500 ms
   - Détection d'un nouveau texte anglais (heuristique simple : ratio de mots anglais)
   - Notification Toast via `QSystemTrayIcon.showMessage()` : "Nouveau texte détecté — Traduire ?"
   - Bouton "Oui" dans la notification → traduction automatique

2. **Historique des traductions** :
   - Stockage SQLite : `(id, source_text, target_text, timestamp, source_lang, target_lang)`
   - Fenêtre dédiée `HistoryWindow` avec recherche full-text
   - Double-clic → rechargement dans la fenêtre principale
   - Nettoyage automatique après 500 entrées (configurable)

3. **Synthèse vocale** :
   - Bouton "Écouter" sur la zone cible
   - Lecture via `espeak-ng -v fr`
   - Bouton "Stop" pour interrompre
   - Indication visuelle pendant la lecture

4. **Thème sombre / clair** :
   - Détection automatique via `QStyleHints.colorScheme()` (Qt 6.5+)
   - Bascule manuelle dans les préférences
   - Palette personnalisée (pas de dépendance à `qdarktheme`)

5. **Export** :
   - Texte traduit → `.txt`
   - Paire source + cible → `.json` structuré
   - Via `QFileDialog.getSaveFileName()`

6. **Raccourcis clavier globaux** :
   - `Ctrl+Return` : lancer la traduction
   - `Ctrl+Shift+C` : copier le résultat
   - `Ctrl+L` : vider les champs
   - `Ctrl+H` : ouvrir l'historique
   - Note : les raccourcis **globaux système** (depuis d'autres applis) nécessitent `python-xlib` et sont complexes sous Wayland — à traiter en v2.

---

## 5. Interface utilisateur

```
┌─────────────────────────────────────────────────────────┐
│  [⚙ Config]  [📋 Historique]  [🌙 Thème]        LibreTrador │
├────────────────────────────┬────────────────────────────┤
│  🇬🇧 Anglais (source)      │  🇫🇷 Français (cible)       │
│                            │                            │
│  [Zone de texte éditable]  │  [Zone lecture seule]      │
│                            │                            │
│  1 247 / 5 000 car.        │  [🔊 Écouter]  [📋 Copier] │
├────────────────────────────┴────────────────────────────┤
│  [📂 Fichier]  [🔄 Traduire]  [✖ Effacer]  [💾 Exporter]│
├─────────────────────────────────────────────────────────┤
│  ● Moteur : Argos EN→FR  |  Modèle v1.9  |  v0.1.0    │
└─────────────────────────────────────────────────────────┘
```

- **Disposition** : deux panneaux côte à côte, séparateur redimensionnable (`QSplitter`)
- **Barre d'outils** : en haut (config, historique, thème)
- **Barre d'actions** : en bas des zones (fichier, traduire, effacer, exporter)
- **Barre de statut** : tout en bas (état du moteur, version du modèle, version app)
- **Feedback visuel** :
  - Spinner `QMovie` pendant la traduction
  - Bordure verte sur la zone cible si succès
  - Bordure rouge + message d'erreur si échec
  - `QProgressBar` pour les fichiers longs

---

## 6. Spécificités Linux

### Chemins XDG (via `pathlib`)
```python
# config.py
from pathlib import Path
import os

XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA   = Path(os.environ.get("XDG_DATA_HOME",   Path.home() / ".local/share"))

CONFIG_DIR   = XDG_CONFIG / "libretrador"
DATA_DIR     = XDG_DATA   / "libretrador"
DB_PATH      = DATA_DIR   / "history.db"
MODELS_DIR   = DATA_DIR   / "argos-models"
LOG_FILE     = DATA_DIR   / "libretrador.log"
```

### Fichier `.desktop`
```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=LibreTrador
Comment=Traducteur Anglais → Français hors-ligne
Exec=/usr/bin/libretrador
Icon=libretrador
Categories=Office;Translation;Utility;
Keywords=translation;translate;anglais;français;offline;
StartupNotify=true
```

### Tray Icon
- `QSystemTrayIcon` avec menu contextuel : Afficher / Masquer, Quitter
- Fermeture de la fenêtre → réduit dans le tray (pas de quitter)
- Double-clic tray → restaure la fenêtre

### Icônes
- `assets/libretrador.svg` (vectoriel, thème neutre)
- `assets/libretrador_16.png`, `_32.png`, `_48.png`, `_128.png`
- Compatibles Adwaita et Breeze

---

## 7. Structure du code

```
libretrador/
├── main.py                  # Point d'entrée, QApplication
├── config.py                # Constantes, chemins XDG, version
├── ui/
│   ├── main_window.py       # Fenêtre principale, layout
│   ├── history_window.py    # Fenêtre historique
│   ├── settings_dialog.py   # Boîte de dialogue préférences
│   ├── model_manager.py     # Dialogue téléchargement modèle Argos
│   └── widgets/
│       ├── text_panel.py    # Widget panneau source/cible
│       └── status_bar.py    # Barre de statut personnalisée
├── core/
│   ├── translator.py        # Wrapper Argos Translate + QThread worker
│   ├── clipboard.py         # Surveillance presse-papier (QTimer)
│   ├── database.py          # CRUD SQLite historique
│   ├── tts.py               # Synthèse vocale espeak-ng
│   └── file_reader.py       # Lecture .txt / .docx / .pdf
├── assets/
│   ├── libretrador.svg
│   ├── libretrador_48.png
│   └── libretrador_128.png
├── requirements.txt
├── requirements-dev.txt     # black, flake8, pytest
├── libretrador.desktop
├── debian/                  # Packaging .deb
│   ├── control
│   ├── changelog
│   ├── rules
│   └── postinst             # sudo apt install espeak-ng si absent
├── build_deb.sh             # Script de build identique à Dessinator
├── README.md
└── CHANGELOG.md
```

---

## 8. Module core/translator.py (architecture)

```python
# Pattern recommandé : QThread pour ne pas bloquer l'UI

from PyQt6.QtCore import QThread, pyqtSignal
import argostranslate.translate as argt

class TranslationWorker(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)  # Pour les fichiers longs

    def __init__(self, text: str, chunks: list[str] = None):
        super().__init__()
        self.text = text
        self.chunks = chunks  # None = texte simple, liste = fichier

    def run(self):
        try:
            if self.chunks:
                results = []
                for i, chunk in enumerate(self.chunks):
                    results.append(argt.translate(chunk, "en", "fr"))
                    self.progress_updated.emit(int((i+1)/len(self.chunks)*100))
                self.result_ready.emit("\n\n".join(results))
            else:
                result = argt.translate(self.text, "en", "fr")
                self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
```

---

## 9. Dépendances et installation

### requirements.txt
```
PyQt6>=6.5.0
argostranslate>=1.9.0
python-docx>=1.1.0
pypdf>=4.0.0
```

### requirements-dev.txt
```
black>=24.0
flake8>=7.0
pytest>=8.0
pytest-qt>=4.4
```

### Dépendances système (Debian)
```bash
sudo apt install python3-pyqt6 espeak-ng libespeak-ng1
```

> À documenter dans le README et à vérifier/installer dans le script `postinst` du paquet `.deb`.

---

## 10. Packaging .deb (workflow GitHub)

Identique au workflow de Dessinator et rssnews :

1. `build_deb.sh` compile le paquet
2. Tag Git `vX.Y.Z` → GitHub Actions crée la Release
3. Le `.deb` est attaché à la Release comme artefact téléchargeable
4. `debian/postinst` vérifie et installe `espeak-ng` si absent

---

## 11. Points de vigilance

| Risque | Mitigation |
|---|---|
| Modèle Argos absent au premier lancement | Dialogue `ModelManagerDialog` avec barre de progression du téléchargement |
| Texte trop long → freeze UI | `QThread` obligatoire pour toute traduction |
| Wayland : tray icon instable | Tester avec `QT_QPA_PLATFORM=xcb` en fallback, documenter |
| `espeak-ng` absent sur le système | Vérification au démarrage, message d'erreur actionnable |
| Traduction de PDF scannés | Hors scope MVP — PDF texte uniquement via pypdf |
| Surveillance clipboard Wayland | `QTimer` + `QApplication.clipboard()` fonctionne, mais les notifs système peuvent être bloquées selon le compositeur |

---

## 12. Roadmap suggérée

| Version | Contenu |
|---|---|
| **v0.1.0** | MVP : traduction texte + copier/effacer/compteur + historique SQLite |
| **v0.2.0** | Traduction fichiers .txt + export .txt/.json + thème sombre |
| **v0.3.0** | TTS espeak-ng + surveillance clipboard + notifications tray |
| **v1.0.0** | Traduction .docx et .pdf + packaging .deb + GitHub Release |
