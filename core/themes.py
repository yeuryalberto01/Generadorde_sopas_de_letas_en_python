"""Gestión de temas y sus palabras asociadas."""

from __future__ import annotations

from typing import List, Optional, Tuple

from .db import get_conn
from .lexicon import validate_word


def create_theme(name: str, description: str | None = None) -> int:
    if not name or not name.strip():
        raise ValueError("El nombre del tema no puede estar vacío.")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO themes (name, description) VALUES (?, ?);",
            (name.strip(), description),
        )
        return cur.lastrowid


def update_theme(theme_id: int, name: str, description: str | None = None) -> None:
    if not name or not name.strip():
        raise ValueError("El nombre del tema no puede estar vacío.")
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE themes SET name = ?, description = ? WHERE id = ?;",
            (name.strip(), description, theme_id),
        )
        if cur.rowcount == 0:
            raise ValueError(f"No existe el tema con id {theme_id}.")


def delete_theme(theme_id: int) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM words WHERE theme_id = ?;", (theme_id,))
        cur.execute("DELETE FROM themes WHERE id = ?;", (theme_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No existe el tema con id {theme_id}.")


def list_themes() -> List[Tuple[int, str, Optional[str]]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description FROM themes ORDER BY name COLLATE NOCASE;"
        )
        return cur.fetchall()


def add_word_to_theme(theme_id: int, raw_word: str) -> int:
    result = validate_word(raw_word)
    if not result.valid:
        raise ValueError("; ".join(result.errors))
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM themes WHERE id = ?;", (theme_id,))
        if cur.fetchone() is None:
            raise ValueError(f"No existe el tema con id {theme_id}.")
        cur.execute(
            "INSERT INTO words (theme_id, word, original) VALUES (?, ?, ?);",
            (theme_id, result.normalized, result.original),
        )
        return cur.lastrowid


def delete_word(word_id: int) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM words WHERE id = ?;", (word_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No existe la palabra con id {word_id}.")


def get_words_for_theme(theme_id: int) -> List[Tuple[int, str, str]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, word, COALESCE(original, word) FROM words WHERE theme_id = ? ORDER BY word;",
            (theme_id,),
        )
        return cur.fetchall()


__all__ = [
    "create_theme",
    "update_theme",
    "delete_theme",
    "list_themes",
    "add_word_to_theme",
    "delete_word",
    "get_words_for_theme",
]
