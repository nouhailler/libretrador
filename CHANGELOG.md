# CHANGELOG

## [0.1.0] — 2026-03-22

### Ajouté
- MVP complet : traduction texte Anglais → Français via Argos Translate
- Interface PyQt6 avec deux panneaux côte à côte (QSplitter)
- Boutons Traduire, Copier, Effacer, Exporter (.txt / .json)
- Compteur de caractères avec limite indicative de 5 000 car.
- Historique SQLite (fenêtre dédiée, recherche, double-clic pour recharger)
- Traduction de fichiers .txt avec barre de progression
- Synthèse vocale via espeak-ng (`🔊 Écouter`)
- Surveillance optionnelle du presse-papier (détection heuristique anglais)
- Icône dans la barre système (QSystemTrayIcon), fermeture → masquage
- Dialogue d'installation du modèle Argos au premier lancement
- Raccourcis clavier : Ctrl+Entrée, Ctrl+Shift+C, Ctrl+L, Ctrl+H
- Chemins XDG (config, données, BDD, logs)
- Fichier `.desktop` pour intégration dans les menus DE
