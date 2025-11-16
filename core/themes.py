"""Gestión de temas y glosarios persistidos en SQLite."""

from __future__ import annotations

from typing import List, Tuple

from .db import get_conn
from .lexicon import validate_word


def create_theme(name: str, description: str | None = None) -> int:
    """Crea un tema y devuelve su ID."""
    if not name.strip():
        raise ValueError("El nombre del tema no puede estar vacío.")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO themes (name, description) VALUES (?, ?)",
            (name.strip(), description),
        )
        return cur.lastrowid


def add_word_to_theme(theme_id: int, word: str) -> int:
    """Agrega una palabra validada a un tema existente."""
    result = validate_word(word)
    if not result.valid:
        raise ValueError("; ".join(result.errors))

    with get_conn() as conn:
        cur = conn.cursor()
        # asegurar que el tema existe
        cur.execute("SELECT id FROM themes WHERE id = ?", (theme_id,))
        if cur.fetchone() is None:
            raise ValueError(f"No existe el tema con id {theme_id}.")
        cur.execute(
            "INSERT INTO words (theme_id, word) VALUES (?, ?)",
            (theme_id, result.normalized),
        )
        return cur.lastrowid


def list_themes() -> List[Tuple[int, str, str | None]]:
    """Lista todos los temas registrados."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description FROM themes ORDER BY name COLLATE NOCASE"
        )
        return cur.fetchall()


def get_words_for_theme(theme_id: int) -> List[str]:
    """Devuelve las palabras asociadas a un tema."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT word FROM words WHERE theme_id = ? ORDER BY word ASC",
            (theme_id,),
        )
        rows = cur.fetchall()
    return [row[0] for row in rows]


__all__ = [
    "create_theme",
    "add_word_to_theme",
    "list_themes",
    "get_words_for_theme",
]
