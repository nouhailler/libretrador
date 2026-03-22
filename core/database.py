"""CRUD SQLite pour l'historique des traductions."""

import sqlite3
import logging
from datetime import datetime
from config import DB_PATH, MAX_HISTORY

logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée les tables si elles n'existent pas, et migre si nécessaire."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT    NOT NULL,
                target_text TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL,
                source_lang TEXT    DEFAULT 'en',
                target_lang TEXT    DEFAULT 'fr',
                direction   TEXT    DEFAULT 'en→fr'
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp DESC)"
        )
        # Migration : ajouter la colonne direction si absente (tables existantes)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(history)")}
        if "direction" not in cols:
            conn.execute("ALTER TABLE history ADD COLUMN direction TEXT DEFAULT 'en→fr'")
        conn.commit()


def save_translation(source: str, target: str,
                     src_lang: str = "en", tgt_lang: str = "fr"):
    """Insère une paire source/cible et nettoie si nécessaire."""
    direction = f"{src_lang}→{tgt_lang}"
    with _connect() as conn:
        conn.execute(
            "INSERT INTO history "
            "(source_text, target_text, timestamp, source_lang, target_lang, direction) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (source, target, datetime.now().isoformat(), src_lang, tgt_lang, direction),
        )
        conn.commit()
    _cleanup()


def _cleanup():
    """Supprime les entrées les plus anciennes si MAX_HISTORY est dépassé."""
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        if count > MAX_HISTORY:
            excess = count - MAX_HISTORY
            conn.execute("""
                DELETE FROM history WHERE id IN (
                    SELECT id FROM history ORDER BY timestamp ASC LIMIT ?
                )
            """, (excess,))
            conn.commit()


def get_history(limit: int = 200, offset: int = 0,
                search: str = None) -> list[dict]:
    """Retourne des entrées d'historique, avec recherche full-text optionnelle."""
    with _connect() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM history "
                "WHERE source_text LIKE ? OR target_text LIKE ? "
                "ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (f"%{search}%", f"%{search}%", limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    return [dict(r) for r in rows]


def delete_entry(entry_id: int):
    """Supprime une entrée par son ID."""
    with _connect() as conn:
        conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
        conn.commit()


def clear_history():
    """Vide entièrement la table historique."""
    with _connect() as conn:
        conn.execute("DELETE FROM history")
        conn.commit()
