"""Fenêtre d'aide de LibreTrador."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTextBrowser, QListWidget, QListWidgetItem,
    QPushButton, QSplitter,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import APP_NAME, APP_VERSION
from core.ollama_engine import DEFAULT_MODEL, OLLAMA_BASE_URL
from core.tts import PIPER_BIN, PIPER_MODEL


# ──────────────────────────────────────────────────────────────────────
# Contenu de l'aide par section
# Chaque entrée : (titre_menu, contenu_HTML)
# ──────────────────────────────────────────────────────────────────────

def _sections() -> list[tuple[str, str]]:
    return [
        ("Vue d'ensemble",              _s_overview()),
        ("Traduction de texte",         _s_text()),
        ("Direction de traduction",     _s_direction()),
        ("Moteurs de traduction",       _s_engines()),
        ("Glossaire personnalisé",      _s_glossary()),
        ("Synonymes",                   _s_synonyms()),
        ("Traduction de fichiers",      _s_files()),
        ("Sous-titres SRT",             _s_srt()),
        ("Historique",                  _s_history()),
        ("Synthèse vocale",             _s_tts()),
        ("Presse-papier auto",          _s_clipboard()),
        ("Exporter",                    _s_export()),
        ("Raccourcis clavier",          _s_shortcuts()),
        ("Préférences",                 _s_settings()),
        ("À propos",                    _s_about()),
    ]


# ──────────────────────────────────────────────────────────────────────
# CSS interne du QTextBrowser (indépendant du thème QSS de l'app)
# ──────────────────────────────────────────────────────────────────────

_CSS = """
body        { font-family: 'Noto Sans', sans-serif; font-size: 13px;
              line-height: 1.6; margin: 16px 20px; }
h1          { font-size: 18px; margin-bottom: 4px; }
h2          { font-size: 14px; margin-top: 18px; margin-bottom: 4px; }
p           { margin: 6px 0; }
ul          { margin: 4px 0 8px 0; padding-left: 20px; }
li          { margin: 3px 0; }
kbd         { font-family: monospace; padding: 2px 6px;
              border-radius: 4px; font-size: 12px; }
code        { font-family: monospace; padding: 1px 5px;
              border-radius: 3px; font-size: 12px; }
.tip        { border-left: 3px solid #7c6af7; padding: 6px 12px;
              border-radius: 0 6px 6px 0; margin: 10px 0; }
.warn       { border-left: 3px solid #f38ba8; padding: 6px 12px;
              border-radius: 0 6px 6px 0; margin: 10px 0; }
.ok         { border-left: 3px solid #a8e063; padding: 6px 12px;
              border-radius: 0 6px 6px 0; margin: 10px 0; }
table       { border-collapse: collapse; width: 100%; margin: 10px 0; }
th          { padding: 6px 12px; text-align: left; font-weight: bold; }
td          { padding: 5px 12px; }
"""


def _html(title: str, body: str) -> str:
    return f"<html><head><style>{_CSS}</style></head><body><h1>{title}</h1>{body}</body></html>"


# ──────────────────────────────────────────────────────────────────────
# Sections
# ──────────────────────────────────────────────────────────────────────

def _s_overview() -> str:
    return _html("Vue d'ensemble", """
<p><b>LibreTrador</b> est un traducteur <b>hors-ligne Anglais ↔ Français</b>
pour Linux. Tout le traitement s'effectue localement — aucune donnée n'est envoyée
à un service externe.</p>

<h2>Interface principale</h2>
<ul>
  <li><b>Panneau gauche</b> — zone de saisie du texte source (éditable)</li>
  <li><b>Panneau droit</b> — résultat de la traduction (éditable pour corrections)</li>
  <li><b>Bouton ⇄</b> — inverse la direction de traduction, centré sur le séparateur</li>
  <li><b>Barre d'outils</b> (haut) — Config · Historique · Aide · Sélecteur de moteur</li>
  <li><b>Barre d'actions</b> (bas) — Fichier · Traduire · Tout effacer · Exporter</li>
  <li><b>Barre de statut</b> (tout en bas) — état du moteur et direction active</li>
</ul>

<div class="tip">
  💡 Le séparateur central est <b>redimensionnable</b> : faites-le glisser
  pour agrandir l'un des deux panneaux. Le bouton ⇄ reste centré sur le séparateur.
</div>

<h2>Premier lancement</h2>
<p>Si le modèle Argos Translate EN→FR n'est pas encore installé, une fenêtre de
téléchargement s'affiche automatiquement. Le modèle (~100 Mo) est
téléchargé une seule fois et stocké dans
<code>~/.local/share/libretrador/</code>.</p>
""")


def _s_text() -> str:
    return _html("Traduction de texte", """
<h2>Saisir du texte</h2>
<p>Tapez ou collez du texte dans le <b>panneau gauche</b>.
Un compteur affiche le nombre de caractères saisis.</p>
<ul>
  <li>Limite indicative : <b>5 000 caractères</b> pour le moteur Argos</li>
  <li>Le moteur Ollama n'a pas de limite stricte</li>
</ul>

<h2>Lancer la traduction</h2>
<p>Cliquez sur <b>🔄 Traduire</b> ou appuyez sur <kbd>Ctrl</kbd>+<kbd>Entrée</kbd>.</p>
<p>La traduction s'exécute en arrière-plan — l'interface reste réactive pendant le calcul.</p>

<h2>Indicateurs visuels</h2>
<ul>
  <li><b>Bordure verte</b> sur le panneau droit → traduction réussie</li>
  <li><b>Bordure rouge</b> → une erreur s'est produite (voir la barre de statut)</li>
  <li><b>Bouton grisé</b> → traduction en cours, patientez</li>
</ul>

<h2>Modifier la traduction</h2>
<p>Le panneau droit est <b>éditable</b> : vous pouvez corriger ou compléter
la traduction obtenue directement dans la zone de texte.</p>
<p>Utilisez ensuite le bouton <b>⇄</b> pour basculer le résultat corrigé
côté source et le retraduire dans l'autre sens si besoin.</p>

<h2>Copier le résultat</h2>
<p>Cliquez sur <b>📋 Copier</b> (panneau droit) ou <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>C</kbd>
pour placer la traduction dans le presse-papier.</p>

<h2>Effacer les panneaux</h2>
<ul>
  <li>Le petit bouton <b>✖</b> dans l'en-tête de chaque panneau efface
      <em>uniquement ce panneau</em></li>
  <li>Le bouton <b>✖ Tout effacer</b> (barre du bas) ou <kbd>Ctrl</kbd>+<kbd>L</kbd>
      vide les deux panneaux en une fois</li>
</ul>
""")


def _s_direction() -> str:
    return _html("Direction de traduction", """
<h2>Traduction bidirectionnelle EN ↔ FR</h2>
<p>LibreTrador supporte la traduction dans les deux sens :</p>
<ul>
  <li><b>EN → FR</b> : Anglais vers Français (direction par défaut)</li>
  <li><b>FR → EN</b> : Français vers Anglais</li>
</ul>

<h2>Changer de direction — bouton ⇄</h2>
<p>Cliquez sur le bouton <b>⇄</b> centré sur le séparateur entre les deux panneaux.
Il effectue simultanément :</p>
<ul>
  <li>L'inversion de la direction de traduction</li>
  <li>L'échange du contenu des deux panneaux (le texte traduit passe à gauche)</li>
  <li>La mise à jour des titres et des libellés du moteur</li>
  <li>La mise à jour de la barre de statut</li>
</ul>

<div class="tip">
  💡 Le choix de direction est mémorisé entre les sessions.
</div>

<h2>Modèles Argos requis</h2>
<p>Chaque direction nécessite son propre modèle Argos Translate :</p>
<ul>
  <li><b>EN→FR</b> : téléchargé automatiquement au premier lancement</li>
  <li><b>FR→EN</b> : proposé au téléchargement lors du premier usage de cette direction</li>
</ul>
<p>Chaque modèle pèse environ <b>100 Mo</b> et est installé une seule fois dans
<code>~/.local/share/argos-translate/packages/</code>.</p>

<div class="warn">
  ⚠️ Si le modèle pour la direction sélectionnée n'est pas installé,
  le bouton Traduire est désactivé et LibreTrador propose le téléchargement.
</div>

<h2>Moteur Ollama et direction</h2>
<p>Le moteur Ollama s'adapte automatiquement à la direction sélectionnée :
il utilise un prompt système différent selon que vous traduisez EN→FR ou FR→EN.
Aucun modèle supplémentaire à télécharger pour Ollama.</p>

<h2>Historique et direction</h2>
<p>Chaque entrée de l'historique enregistre la direction de traduction utilisée
(colonne <b>Direction</b> dans la fenêtre Historique).</p>
""")


def _s_engines() -> str:
    return _html("Moteurs de traduction", f"""
<p>LibreTrador propose deux moteurs sélectionnables via le menu déroulant
<b>« Moteur »</b> dans la barre d'outils. Le libellé indique la direction active.</p>

<h2>⚡ Argos Translate — moteur rapide</h2>
<ul>
  <li>Idéal pour les textes courts (&lt; 500 caractères)</li>
  <li>Réponse quasi-instantanée</li>
  <li>Fonctionne sans aucune dépendance externe au-delà du modèle installé</li>
  <li>Qualité correcte pour des phrases isolées</li>
  <li>Supporte les deux directions : EN→FR et FR→EN (modèles séparés)</li>
</ul>

<h2>🧠 Ollama — moteur qualité</h2>
<ul>
  <li>Idéal pour les textes longs, les fichiers et les tournures idiomatiques</li>
  <li>Modèle par défaut : <code>{DEFAULT_MODEL}</code></li>
  <li>Requiert qu'<b>Ollama</b> tourne localement sur <code>{OLLAMA_BASE_URL}</code></li>
  <li>Si Ollama n'est pas détecté, l'option est <b>grisée</b> dans le sélecteur</li>
  <li>Un seul modèle gère les deux directions (prompt adapté automatiquement)</li>
</ul>

<div class="tip">
  💡 Pour les fichiers de plusieurs paragraphes, LibreTrador vous suggère
  automatiquement de basculer sur Ollama si ce moteur est disponible.
</div>

<h2>Changer de modèle Ollama</h2>
<p>Le nom du modèle est configurable dans <b>⚙ Config → Moteur Ollama → Modèle</b>.
Tout modèle installé via <code>ollama pull nom-du-modèle</code> peut être utilisé.</p>

<table>
  <tr><th>Critère</th><th>Argos</th><th>Ollama {DEFAULT_MODEL}</th></tr>
  <tr><td>Textes courts</td><td>✅ Idéal</td><td>✅</td></tr>
  <tr><td>Textes longs / fichiers</td><td>⚠️ Limité</td><td>✅ Idéal</td></tr>
  <tr><td>Vitesse</td><td>⚡ Très rapide</td><td>🐢 Plus lent</td></tr>
  <tr><td>Qualité</td><td>★★★☆☆</td><td>★★★★★</td></tr>
  <tr><td>Hors-ligne</td><td>✅</td><td>✅ (modèle local)</td></tr>
  <tr><td>Bidirectionnel</td><td>✅ (2 modèles)</td><td>✅ (1 modèle)</td></tr>
</table>
""")


def _s_glossary() -> str:
    return _html("Glossaire personnalisé", """
<h2>Principe</h2>
<p>Le glossaire vous permet de définir des <b>règles de remplacement</b> appliquées
<i>automatiquement après chaque traduction</i>. Utile pour :</p>
<ul>
  <li>Les <b>termes techniques</b> mal traduits par les moteurs ("Cloud" → "Nuage")</li>
  <li>Les <b>noms propres</b> à conserver intacts ou à transcrire d'une façon précise</li>
  <li>Le <b>jargon d'entreprise</b> ou le vocabulaire métier spécifique</li>
  <li>Les <b>acronymes</b> à ne jamais traduire (ex. "API" → "API")</li>
</ul>

<h2>Ouvrir le glossaire</h2>
<p>Cliquez sur <b>📖 Glossaire</b> dans la barre d'outils.
Le glossaire est <b>propre à chaque direction</b> (EN→FR et FR→EN ont chacun leur fichier).</p>

<h2>Colonnes du tableau</h2>
<table>
  <tr><th>Colonne</th><th>Description</th></tr>
  <tr><td>✓</td><td>Règle active (décochez pour désactiver sans supprimer)</td></tr>
  <tr><td>Terme à rechercher</td><td>Le mot ou groupe de mots à trouver dans la traduction</td></tr>
  <tr><td>Remplacer par</td><td>Le texte de remplacement (peut être vide pour supprimer le terme)</td></tr>
  <tr><td>Mot entier</td><td>Coché = ne remplace que si c'est un mot isolé (évite "Cloud" dans "CloudWatch")</td></tr>
  <tr><td>Casse exacte</td><td>Coché = respecte la casse ("Cloud" ≠ "cloud")</td></tr>
</table>

<h2>Ajouter / modifier une règle</h2>
<ul>
  <li>Cliquez sur <b>＋ Ajouter une règle</b> pour insérer une ligne vide</li>
  <li><b>Double-cliquez</b> sur une cellule "Terme" ou "Remplacer par" pour l'éditer</li>
  <li>Utilisez <b>↑ / ↓</b> pour réordonner les règles (l'ordre compte !)</li>
  <li>Cliquez sur <b>OK</b> pour enregistrer — les modifications sont actives immédiatement</li>
</ul>

<div class="tip">
  💡 Les règles sont appliquées <b>dans l'ordre affiché</b>. Placez les règles
  les plus spécifiques en premier pour éviter qu'une règle générale ne les écrase.
</div>

<h2>Ordre de priorité</h2>
<p>Exemple : si vous avez deux règles :</p>
<ul>
  <li>Règle 1 : "cloud computing" → "informatique en nuage"</li>
  <li>Règle 2 : "cloud" → "nuage"</li>
</ul>
<p>En plaçant la règle 1 <b>avant</b> la règle 2, "cloud computing" sera correctement
remplacé avant que la règle 2 ne traite les "cloud" restants.</p>

<h2>Import / Export JSON</h2>
<p>Vous pouvez partager ou sauvegarder vos glossaires via des fichiers JSON :</p>
<ul>
  <li><b>📂 Importer JSON</b> — ajouter ou remplacer les règles depuis un fichier</li>
  <li><b>💾 Exporter JSON</b> — sauvegarder les règles dans un fichier</li>
</ul>

<p>Format du fichier :</p>
<pre><code>[
  {
    "term": "Cloud",
    "replacement": "Nuage",
    "enabled": true,
    "whole_word": true,
    "case_sensitive": false
  },
  {
    "term": "API",
    "replacement": "API",
    "enabled": true,
    "whole_word": true,
    "case_sensitive": true
  }
]</code></pre>

<h2>Stockage</h2>
<p>Les glossaires sont sauvegardés dans :</p>
<ul>
  <li><code>~/.config/libretrador/glossary_en_fr.json</code> — direction EN→FR</li>
  <li><code>~/.config/libretrador/glossary_fr_en.json</code> — direction FR→EN</li>
</ul>

<div class="warn">
  ⚠️ Si "Mot entier" est décoché, le terme est cherché partout dans le texte,
  y compris à l'intérieur d'autres mots. Utilisez cette option avec précaution
  pour les termes très courts (ex. "a", "le", "to").
</div>
""")


def _s_synonyms() -> str:
    return _html("Synonymes", """
<h2>Principe</h2>
<p>Dans n'importe quelle zone de texte (source ou cible),
faites un <b>clic droit sur un mot</b> pour voir ses synonymes
dans la langue du panneau (anglais ou français).</p>

<p>Cliquer sur un synonyme <b>remplace uniquement le mot sélectionné</b>
— le reste du texte n'est pas touché.</p>

<h2>Utilisation</h2>
<ol>
  <li>Clic droit sur un mot dans le panneau source ou cible</li>
  <li>Le menu affiche jusqu'à <b>10 synonymes</b> sous l'entrée
      <em>« Synonymes de … »</em></li>
  <li>Cliquez sur le synonyme de votre choix pour remplacer le mot</li>
</ol>

<div class="tip">
  💡 La recherche de synonymes tient compte de la direction active :
  le panneau gauche cherche dans la langue source (EN ou FR),
  le panneau droit dans la langue cible (FR ou EN).
  Les langues s'inversent automatiquement avec le bouton ⇄.
</div>

<h2>Moteur — NLTK WordNet</h2>
<p>Les synonymes proviennent de <b>WordNet</b> via la bibliothèque NLTK :</p>
<ul>
  <li>Anglais : corpus <code>wordnet</code> (Princeton WordNet)</li>
  <li>Français : corpus <code>omw-1.4</code> (Open Multilingual Wordnet)</li>
</ul>
<p>Les données sont téléchargées <b>une seule fois</b> par <code>setup.sh</code>
et stockées dans le virtualenv — aucune connexion réseau lors de l'utilisation.</p>

<h2>Comportement selon le mot</h2>
<ul>
  <li>Seuls les mots alphabétiques déclenchent la recherche
      (les nombres, ponctuations et symboles sont ignorés)</li>
  <li>La recherche porte sur les <b>4 premiers ensembles lexicaux</b>
      (synsets) pour limiter le bruit</li>
  <li>Si aucun synonyme n'est trouvé, le menu affiche
      <em>« (aucun synonyme trouvé) »</em></li>
</ul>

<div class="warn">
  ⚠️ Si les données WordNet n'ont pas été téléchargées (setup.sh non relancé
  depuis la mise à jour), le menu contextuel affiche simplement
  « (aucun synonyme trouvé) » sans message d'erreur.
</div>
""")


def _s_files() -> str:
    return _html("Traduction de fichiers", """
<h2>Ouvrir un fichier</h2>
<p>Cliquez sur <b>📂 Fichier</b> pour ouvrir un fichier à traduire.
La direction de traduction active (EN→FR ou FR→EN) s'applique.</p>

<p>Formats supportés :</p>
<ul>
  <li><code>.txt</code> — fichier texte brut (découpage par paragraphes)</li>
  <li><code>.docx</code> — document Word (paragraphes extraits)</li>
  <li><code>.pdf</code> — PDF texte uniquement (PDF scannés non supportés)</li>
  <li><code>.srt</code> — fichier de sous-titres (voir section dédiée)</li>
</ul>

<h2>Progression</h2>
<p>Pour les fichiers multi-paragraphes, une <b>barre de progression</b> fine
apparaît sous les panneaux. Chaque paragraphe est traduit séquentiellement.</p>

<div class="tip">
  💡 Pour les fichiers longs, utilisez le moteur <b>Ollama</b> pour
  une meilleure qualité. LibreTrador vous le suggère automatiquement.
</div>

<div class="warn">
  ⚠️ Les PDF scannés (images) ne sont pas supportés. Seuls les PDF
  contenant du texte sélectionnable peuvent être traduits.
</div>

<h2>Aperçu dans le panneau source</h2>
<p>Les 3 premiers paragraphes du fichier s'affichent dans le panneau gauche
à titre d'aperçu. Le texte traduit complet apparaît dans le panneau droit.</p>
""")


def _s_srt() -> str:
    return _html("Sous-titres SRT", """
<h2>Traduction de fichiers de sous-titres</h2>
<p>LibreTrador traduit les fichiers <code>.srt</code> en préservant intégralement
la structure : numéros de blocs, timecodes et retours à la ligne.
Seul le texte des sous-titres est traduit.</p>

<h2>Comment utiliser</h2>
<ol>
  <li>Cliquez sur <b>📂 Fichier</b> et sélectionnez un fichier <code>.srt</code></li>
  <li>Le panneau source affiche le nombre de blocs détectés et un aperçu des 3 premiers</li>
  <li>La traduction démarre automatiquement avec le moteur sélectionné</li>
  <li>Une fois terminée, une boîte de dialogue propose d'enregistrer le fichier traduit</li>
  <li>Le nom suggéré ajoute le code langue cible au nom original
      (ex. <code>film_FR.srt</code>)</li>
</ol>

<h2>Stratégies de traduction selon le moteur</h2>
<p>Les deux moteurs utilisent des approches différentes, adaptées à leurs contraintes :</p>

<h2>⚡ Argos — traduction bloc par bloc</h2>
<p>Argos traduit chaque sous-titre <b>individuellement</b>, sans regroupement.
Argos étant quasi instantané par appel (traitement local CPU), le coût de
N appels séparés est négligeable même pour des fichiers de plusieurs centaines de blocs.</p>
<ul>
  <li>Aucun risque de corruption des séparateurs</li>
  <li>Progression en temps réel bloc par bloc</li>
  <li>Idéal pour les fichiers de taille petite à moyenne</li>
</ul>

<h2>🧠 Ollama — chunking avec marqueur §§§</h2>
<p>Ollama regroupe plusieurs blocs en un seul appel (jusqu'à 1 500 caractères),
séparés par le marqueur interne <code>§§§</code>, pour réduire le nombre d'appels
réseau et améliorer la cohérence contextuelle entre les sous-titres.</p>
<ul>
  <li>Le prompt système demande explicitement à Ollama de <b>conserver §§§ intact</b></li>
  <li>Après traduction, le nombre de <code>§§§</code> reçus est vérifié :
      s'il diffère du nombre attendu, le chunk est <b>retraité bloc par bloc</b>
      automatiquement</li>
  <li>Meilleure cohérence sur les dialogues longs grâce au contexte multi-blocs</li>
</ul>

<div class="tip">
  💡 Pour les fichiers de plus de 20 blocs, <b>Ollama</b> est recommandé :
  meilleure cohérence entre les répliques et respect du registre de langue.
  LibreTrador vous le suggère automatiquement.
</div>

<h2>Encodages supportés</h2>
<p>LibreTrador essaie dans l'ordre : <code>UTF-8 BOM</code>, <code>UTF-8</code>,
<code>Latin-1</code>. Le fichier de sortie est toujours sauvegardé en <b>UTF-8</b>.</p>

<h2>Gestion des erreurs</h2>
<table>
  <tr><th>Situation</th><th>Comportement</th></tr>
  <tr><td>Fichier SRT malformé</td><td>Message d'erreur dans le panneau droit, aucune traduction lancée</td></tr>
  <tr><td>Encodage inconnu</td><td>Fallback Latin-1 avec avertissement dans les logs</td></tr>
  <tr><td>Ollama : §§§ altérés</td><td>Retraitement automatique du chunk bloc par bloc</td></tr>
  <tr><td>Bloc vide</td><td>Conservé tel quel dans le fichier de sortie</td></tr>
</table>

<div class="warn">
  ⚠️ Les fichiers <code>.ass</code> / <code>.ssa</code> (sous-titres avec mise en forme
  avancée) ne sont pas supportés. Convertissez-les en <code>.srt</code> au préalable
  avec un outil comme Aegisub ou ffmpeg.
</div>

<h2>Format SRT attendu</h2>
<pre><code>1
00:00:01,000 --> 00:00:03,500
Hello, world!

2
00:00:04,000 --> 00:00:06,000
This is a subtitle file.</code></pre>
""")


def _s_history() -> str:
    return _html("Historique", """
<h2>Accéder à l'historique</h2>
<p>Cliquez sur <b>📋 Historique</b> dans la barre d'outils ou appuyez sur
<kbd>Ctrl</kbd>+<kbd>H</kbd>.</p>

<h2>Fonctionnalités</h2>
<ul>
  <li><b>Liste chronologique</b> de toutes les traductions effectuées</li>
  <li><b>Colonne Direction</b> — indique le sens de traduction utilisé (EN→FR ou FR→EN)</li>
  <li><b>Recherche en temps réel</b> dans les textes source et cible</li>
  <li><b>Double-clic</b> sur une entrée → recharge la paire dans la fenêtre principale</li>
  <li><b>Suppression</b> d'une ou plusieurs entrées sélectionnées</li>
  <li><b>Effacement complet</b> de tout l'historique (avec confirmation)</li>
</ul>

<h2>Stockage</h2>
<p>L'historique est stocké dans une base SQLite :</p>
<p><code>~/.local/share/libretrador/history.db</code></p>

<h2>Limite automatique</h2>
<p>Par défaut, l'historique est limité à <b>500 entrées</b>. Les entrées
les plus anciennes sont supprimées automatiquement au-delà de cette limite.
La limite est configurable dans <b>⚙ Config → Historique</b>.</p>
""")


def _s_tts() -> str:
    return _html("Synthèse vocale", f"""
<h2>Écouter la traduction</h2>
<p>Cliquez sur <b>🔊 Écouter</b> dans le panneau droit pour entendre
la traduction lue à voix haute.</p>

<p>Cliquez sur <b>⏹ Stop</b> (même bouton) pour interrompre la lecture.</p>

<h2>Moteur TTS : Piper</h2>
<p>LibreTrador utilise <b>Piper TTS</b> avec la voix
<code>fr_FR-upmc-medium</code> pour une qualité naturelle.</p>

<p>Piper est exécuté en arrière-plan — l'interface reste utilisable
pendant la lecture audio.</p>

<h2>Prérequis</h2>
<ul>
  <li>Binaire Piper : <code>{PIPER_BIN}</code></li>
  <li>Modèle vocal : <code>{PIPER_MODEL}</code></li>
  <li>Commande système <code>aplay</code> (paquet <code>alsa-utils</code>)</li>
</ul>

<div class="warn">
  ⚠️ Si Piper n'est pas installé, le bouton 🔊 Écouter est désactivé
  et un message apparaît dans la barre de statut au démarrage.
  L'application reste pleinement fonctionnelle pour la traduction.
</div>

<div class="ok">
  ✅ Si Piper est correctement installé, aucune connexion réseau n'est
  nécessaire — la synthèse vocale fonctionne entièrement hors-ligne.
</div>
""")


def _s_clipboard() -> str:
    return _html("Presse-papier automatique", """
<h2>Surveillance du presse-papier</h2>
<p>Quand cette option est activée, LibreTrador surveille le presse-papier
en permanence (toutes les 500 ms).</p>

<p>Si un <b>texte anglais</b> est détecté (heuristique basée sur les mots
courants), il est automatiquement chargé dans le panneau source et une
notification apparaît dans la barre système.</p>

<h2>Activer la surveillance</h2>
<p>Allez dans <b>⚙ Config → Presse-papier</b> et cochez
<em>« Surveiller le presse-papier »</em>.</p>

<div class="tip">
  💡 La détection est heuristique : elle peut rater certains textes courts
  ou des textes contenant peu de mots anglais courants. Pour déclencher
  la traduction manuellement, collez le texte et cliquez sur Traduire.
</div>

<h2>Comportement</h2>
<ul>
  <li>Le texte détecté remplace le contenu du panneau source</li>
  <li>La traduction <b>n'est pas lancée automatiquement</b> — appuyez sur
      <kbd>Ctrl</kbd>+<kbd>Entrée</kbd> pour traduire</li>
  <li>Une notification apparaît dans l'icône de la barre système</li>
</ul>
""")


def _s_export() -> str:
    return _html("Exporter", """
<h2>Exporter la traduction</h2>
<p>Cliquez sur <b>💾 Exporter</b> pour sauvegarder le résultat dans un fichier.
Si vous avez modifié le texte dans le panneau droit, c'est la version modifiée
qui est exportée.</p>

<h2>Formats disponibles</h2>
<ul>
  <li><b>.txt</b> — texte brut, contient uniquement le texte du panneau droit</li>
  <li><b>.json</b> — structure complète avec source, traduction, direction et moteur :</li>
</ul>

<pre><code>{
  "source_lang": "en",
  "target_lang": "fr",
  "direction": "EN→FR",
  "source": "Hello world",
  "translation": "Bonjour le monde",
  "engine": "argos"
}</code></pre>

<p>La boîte de dialogue de sauvegarde propose un emplacement par défaut
dans votre répertoire personnel.</p>
""")


def _s_shortcuts() -> str:
    return _html("Raccourcis clavier", """
<table>
  <tr><th>Raccourci</th><th>Action</th></tr>
  <tr><td><kbd>Ctrl</kbd>+<kbd>Entrée</kbd></td><td>Lancer la traduction</td></tr>
  <tr><td><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>C</kbd></td><td>Copier le résultat</td></tr>
  <tr><td><kbd>Ctrl</kbd>+<kbd>L</kbd></td><td>Tout effacer (les deux panneaux)</td></tr>
  <tr><td><kbd>Ctrl</kbd>+<kbd>H</kbd></td><td>Ouvrir l'historique</td></tr>
  <tr><td><kbd>F1</kbd></td><td>Ouvrir cette aide</td></tr>
  <tr><td><kbd>F2</kbd></td><td>Ouvrir les préférences</td></tr>
</table>

<h2>Effacement individuel des panneaux</h2>
<p>Utilisez le bouton <b>✖</b> dans l'en-tête de chaque panneau pour
n'effacer que ce panneau (pas de raccourci clavier dédié).</p>

<div class="tip">
  💡 Ces raccourcis fonctionnent depuis la fenêtre principale. La fenêtre
  doit être au premier plan pour qu'ils soient actifs.
</div>
""")


def _s_settings() -> str:
    return _html("Préférences", """
<p>Accédez aux préférences via <b>⚙ Config</b> dans la barre d'outils ou
<kbd>F2</kbd>.</p>

<h2>Interface — Thème</h2>
<ul>
  <li><b>🌙 Sombre</b> — fond sombre, texte clair (par défaut)</li>
  <li><b>☀ Clair</b> — fond clair, texte sombre</li>
</ul>
<p>Le thème est appliqué immédiatement à la fermeture du dialogue.</p>

<h2>Presse-papier</h2>
<p>Active ou désactive la surveillance automatique du presse-papier
pour détecter les textes anglais copiés depuis d'autres applications.</p>

<h2>Historique — Limite</h2>
<p>Nombre maximum d'entrées conservées dans la base SQLite (10 à 5 000).
Les plus anciennes sont supprimées automatiquement.</p>

<h2>Moteur Ollama — Modèle</h2>
<p>Nom du modèle Ollama à utiliser. Tout modèle installé localement via
<code>ollama pull</code> peut être renseigné ici.</p>
<p>Exemple : <code>qwen2.5:14b</code>, <code>mistral</code>,
<code>llama3.2</code>…</p>

<h2>Synthèse vocale</h2>
<p>Vitesse de lecture Piper (mots par minute). La valeur par défaut (145)
offre un débit naturel. Augmentez-la pour une lecture plus rapide.</p>
""")


def _s_about() -> str:
    return _html("À propos", f"""
<h2>{APP_NAME} v{APP_VERSION}</h2>
<p>Traducteur hors-ligne Anglais ↔ Français pour Linux.</p>

<h2>Fonctionnalités</h2>
<ul>
  <li>Traduction bidirectionnelle EN↔FR entièrement hors-ligne</li>
  <li>Deux moteurs : Argos Translate (rapide) et Ollama (qualité)</li>
  <li>Glossaire personnalisé (Find &amp; Replace post-traduction, par direction)</li>
  <li>Synonymes via clic droit (WordNet EN et FR, sans connexion réseau)</li>
  <li>Panneaux source et cible tous deux éditables</li>
  <li>Effacement individuel par panneau ou global</li>
  <li>Traduction de fichiers .txt, .docx, .pdf, .srt (sous-titres)</li>
  <li>Historique SQLite avec colonne de direction</li>
  <li>Synthèse vocale hors-ligne via Piper TTS</li>
  <li>Surveillance automatique du presse-papier</li>
  <li>Thèmes sombre et clair</li>
</ul>

<h2>Stack technique</h2>
<ul>
  <li><b>Interface</b> : PyQt6</li>
  <li><b>Traduction rapide</b> : Argos Translate (modèle CTranslate2)</li>
  <li><b>Traduction qualité</b> : Ollama (LLM local)</li>
  <li><b>Synthèse vocale</b> : Piper TTS + aplay</li>
  <li><b>Historique</b> : SQLite (stdlib Python)</li>
  <li><b>Presse-papier</b> : QApplication.clipboard() — compatible Wayland</li>
</ul>

<h2>Données personnelles</h2>
<p>LibreTrador ne collecte aucune donnée. Tout le traitement est local.
Les fichiers de données se trouvent dans :</p>
<ul>
  <li>Configuration : <code>~/.config/libretrador/</code></li>
  <li>Données (historique, modèles) : <code>~/.local/share/libretrador/</code></li>
  <li>Journaux : <code>~/.local/share/libretrador/libretrador.log</code></li>
</ul>

<h2>Licence</h2>
<p>MIT — utilisation, modification et redistribution libres.</p>
""")


# ──────────────────────────────────────────────────────────────────────
# Dialogue principal
# ──────────────────────────────────────────────────────────────────────

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Aide — {APP_NAME}")
        self.setMinimumSize(820, 580)
        self.resize(920, 640)
        self._sections = _sections()
        self._setup_ui()
        self._nav.setCurrentRow(0)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Panneau de navigation (gauche) ────────────────────────────
        self._nav = QListWidget()
        self._nav.setFixedWidth(200)
        self._nav.setFont(QFont("Noto Sans", 11))
        self._nav.setSpacing(2)
        for title, _ in self._sections:
            item = QListWidgetItem(title)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self._nav.addItem(item)
        self._nav.currentRowChanged.connect(self._show_section)
        splitter.addWidget(self._nav)

        # ── Panneau de contenu (droite) ───────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setFont(QFont("Noto Sans", 11))
        splitter.addWidget(self._browser)

        splitter.setSizes([200, 700])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        root.addWidget(splitter)

        # ── Bouton Fermer ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 8, 12, 10)
        btn_row.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.setDefault(True)
        close_btn.setMinimumWidth(90)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _show_section(self, index: int):
        if 0 <= index < len(self._sections):
            _, html = self._sections[index]
            self._browser.setHtml(html)
            self._browser.verticalScrollBar().setValue(0)

    def show_section(self, title: str):
        """Ouvre le dialogue directement sur la section correspondant à `title`."""
        for i, (t, _) in enumerate(self._sections):
            if t == title:
                self._nav.setCurrentRow(i)
                break
