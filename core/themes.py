"""
Gestión de temas, categorías y listas de palabras.

Este módulo proporciona una interfaz para interactuar con el sistema de temas,
que está estructurado en torno a tres conceptos principales:
1.  **Category**: Agrupaciones de alto nivel para los temas (p. ej., "Ciencia").
2.  **Theme**: El tema principal (p. ej., "Planetas"), que contiene metadatos
    y puede pertenecer a una categoría.
3.  **ThemeWordList**: Listas de palabras específicas para un tema, diferenciadas
    por nivel de dificultad (p. ej., "Planetas - Fácil").
"""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .db import get_conn
from .lexicon import validate_word
from .models import Category, Theme, ThemeWordList

logger = logging.getLogger(__name__)

# region Category Management


def create_category(name: str) -> int:
    """Crea una nueva categoría y devuelve su ID."""
    if not name or not name.strip():
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO categories (name) VALUES (?);", (name.strip(),))
            return cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"La categoría '{name.strip()}' ya existe.") from exc


def list_categories() -> List[Category]:
    """Devuelve una lista de todas las categorías."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY name COLLATE NOCASE;")
        rows = cur.fetchall()
        return [Category(**row) for row in rows]


def delete_category(category_id: int) -> None:
    """Elimina una categoría. Los temas asociados quedarán sin categoría."""
    with get_conn() as conn:
        cur = conn.cursor()
        # Los temas no se eliminan, su category_id se pondrá a NULL por la FK.
        cur.execute("DELETE FROM categories WHERE id = ?;", (category_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No existe la categoría con id {category_id}.")


def update_category(category_id: int, name: str) -> None:
    """Actualiza el nombre de una categoría."""
    if not name or not name.strip():
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE categories SET name = ? WHERE id = ?;", (name.strip(), category_id)
            )
            if cur.rowcount == 0:
                raise ValueError(f"No existe la categoría con id {category_id}.")
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"La categoría '{name.strip()}' ya existe.") from exc


# endregion

# region Theme Management


def create_theme(
    name: str,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """Crea un nuevo tema con listas de palabras vacías por defecto y devuelve su ID."""
    if not name or not name.strip():
        raise ValueError("El nombre del tema no puede estar vacío.")
    metadata_json = json.dumps(metadata) if metadata else "{}"
    with get_conn() as conn:
        cur = conn.cursor()
        # Evitar duplicados aún si el esquema previo no tenía UNIQUE.
        cur.execute(
            "SELECT id FROM themes WHERE lower(name) = lower(?);",
            (name.strip(),),
        )
        existing = cur.fetchone()
        if existing:
            logger.warning("Intento de crear tema duplicado: '%s'", name.strip())
            raise ValueError(f"El tema '{name.strip()}' ya existe.")
        try:
            cur.execute(
                """
                INSERT INTO themes (name, description, category_id, metadata_json)
                VALUES (?, ?, ?, ?);
                """,
                (name.strip(), description, category_id, metadata_json),
            )
            theme_id = cur.lastrowid
            # Crear listas de palabras vacías para cada dificultad
            for difficulty in ["fácil", "medio", "difícil"]:
                cur.execute(
                    """
                    INSERT INTO theme_word_lists (theme_id, difficulty, words_json)
                    VALUES (?, ?, ?);
                    """,
                    (theme_id, difficulty, "[]"),
                )
            logger.info("Tema creado: '%s' con ID %d", name.strip(), theme_id)
            return theme_id
        except sqlite3.IntegrityError as exc:
            logger.warning("Intento de crear tema duplicado: '%s'", name.strip())
            raise ValueError(f"El tema '{name.strip()}' ya existe.") from exc


def get_theme(theme_id: int) -> Optional[Theme]:
    """Obtiene un tema completo, con su categoría y listas de palabras."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Obtener el tema y la categoría
        cur.execute(
            """
            SELECT
                t.id, t.name, t.description, t.metadata_json,
                c.id as category_id, c.name as category_name
            FROM themes t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.id = ?;
            """,
            (theme_id,),
        )
        theme_row = cur.fetchone()
        if not theme_row:
            return None

        # Obtener las listas de palabras
        cur.execute(
            """
            SELECT id, theme_id, difficulty, words_json
            FROM theme_word_lists
            WHERE theme_id = ?;
            """,
            (theme_id,),
        )
        word_list_rows = cur.fetchall()

    category = (
        Category(id=theme_row["category_id"], name=theme_row["category_name"])
        if theme_row["category_id"]
        else None
    )

    word_lists = [
        ThemeWordList(
            id=row["id"],
            theme_id=row["theme_id"],
            difficulty=row["difficulty"],
            words=json.loads(row["words_json"]),
        )
        for row in word_list_rows
    ]

    return Theme(
        id=theme_row["id"],
        name=theme_row["name"],
        description=theme_row["description"],
        category=category,
        metadata=json.loads(theme_row["metadata_json"] or "{}"),
        word_lists=word_lists,
    )


def list_themes() -> List[Theme]:
    """Devuelve una lista de todos los temas (sin listas de palabras para eficiencia)."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                t.id, t.name, t.description,
                c.id as category_id, c.name as category_name
            FROM themes t
            LEFT JOIN categories c ON t.category_id = c.id
            ORDER BY t.name COLLATE NOCASE;
            """
        )
        rows = cur.fetchall()

    themes = []
    for row in rows:
        category = (
            Category(id=row["category_id"], name=row["category_name"])
            if row["category_id"]
            else None
        )
        themes.append(
            Theme(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                category=category,
            )
        )
    return themes


def update_theme_details(
    theme_id: int,
    name: str,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
) -> None:
    """Actualiza los detalles básicos de un tema."""
    if not name or not name.strip():
        raise ValueError("El nombre del tema no puede estar vacío.")
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE themes
                SET name = ?, description = ?, category_id = ?
                WHERE id = ?;
                """,
                (name.strip(), description, category_id, theme_id),
            )
            if cur.rowcount == 0:
                raise ValueError(f"No existe el tema con id {theme_id}.")
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                f"El tema '{name.strip()}' ya existe en esta categoría."
            ) from exc


def update_theme_metadata(theme_id: int, metadata: Dict[str, Any]) -> None:
    """Actualiza los metadatos de un tema."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE themes SET metadata_json = ? WHERE id = ?;",
            (json.dumps(metadata), theme_id),
        )
        if cur.rowcount == 0:
            raise ValueError(f"No existe el tema con id {theme_id}.")


def delete_theme(theme_id: int) -> None:
    """Elimina un tema y todas sus listas de palabras asociadas (en cascada)."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM themes WHERE id = ?;", (theme_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No existe el tema con id {theme_id}.")


# endregion

# region Word List Management


def add_or_update_word_list(
    theme_id: int, difficulty: str, words: List[str]
) -> int:
    """
    Agrega o actualiza una lista de palabras para un tema y dificultad.
    Valida y normaliza las palabras antes de guardarlas.
    Devuelve el ID de la fila insertada o actualizada.
    """
    if not difficulty or not difficulty.strip():
        raise ValueError("La dificultad no puede estar vacía.")

    normalized_words = []
    seen_words = set()
    for word in words:
        result = validate_word(word)
        if not result.valid:
            raise ValueError(f"Palabra '{word}' inválida: {'; '.join(result.errors)}")
        if result.normalized in seen_words:
            raise ValueError(f"Palabra duplicada: '{result.normalized}'")
        normalized_words.append(result.normalized)
        seen_words.add(result.normalized)

    if not normalized_words:
        raise ValueError("La lista de palabras no puede estar vacía.")

    words_json = json.dumps(sorted(normalized_words))
    difficulty_clean = difficulty.lower().strip()

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM theme_word_lists WHERE theme_id = ? AND difficulty = ?;",
            (theme_id, difficulty_clean),
        )
        row = cur.fetchone()
        if row:
            # Actualizar
            list_id = row[0]
            cur.execute(
                "UPDATE theme_word_lists SET words_json = ? WHERE id = ?;",
                (words_json, list_id),
            )
            return list_id
        else:
            # Insertar
            cur.execute(
                """
                INSERT INTO theme_word_lists (theme_id, difficulty, words_json)
                VALUES (?, ?, ?);
                """,
                (theme_id, difficulty_clean, words_json),
            )
            return cur.lastrowid


def get_word_list(word_list_id: int) -> Optional[ThemeWordList]:
    """Obtiene una lista de palabras específica por su ID."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM theme_word_lists WHERE id = ?;", (word_list_id,))
        row = cur.fetchone()
        if not row:
            return None
        return ThemeWordList(
            id=row["id"],
            theme_id=row["theme_id"],
            difficulty=row["difficulty"],
            words=json.loads(row["words_json"]),
        )


def delete_word_list(word_list_id: int) -> None:
    """Elimina una lista de palabras específica."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM theme_word_lists WHERE id = ?;", (word_list_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No existe la lista de palabras con id {word_list_id}.")


# endregion

# region Additional Functions for Dialog Compatibility


def update_theme(theme_id: int, name: str, description: Optional[str]) -> None:
    """Alias for update_theme_details for dialog compatibility."""
    update_theme_details(theme_id, name, description)


def get_words_for_theme(
    theme_id: int, difficulty: str = "medio"
) -> List[Tuple[int, str, str]]:
    """Devuelve una lista de tuplas (word_id, normalized, original) para las palabras del tema en la dificultad especificada."""
    theme = get_theme(theme_id)
    if theme is None:
        return []
    words = []
    word_lists = getattr(theme, 'word_lists', [])
    if not isinstance(word_lists, list):
        return []
    for word_list in word_lists:
        if word_list.difficulty == difficulty:
            for idx, word in enumerate(word_list.words):
                word_id = word_list.id * 1000 + idx  # Fake id
                words.append((word_id, word, word))  # normalized and original are the same
            break
    return words


def add_word_to_theme(theme_id: int, word: str, difficulty: str = "medio") -> None:
    """Agrega una palabra a la lista de palabras del tema para la dificultad especificada."""
    # Validate word
    result = validate_word(word)
    if not result.valid:
        raise ValueError("; ".join(result.errors))
    normalized = result.normalized

    # Check if word list exists for the difficulty
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            "SELECT id, words_json FROM theme_word_lists WHERE theme_id = ? AND difficulty = ?;",
            (theme_id, difficulty)
        )
        row = cur.fetchone()
        if row is None:
            # This shouldn't happen since we create all difficulties
            add_or_update_word_list(theme_id, difficulty, [normalized])
        else:
            # Add to existing list if not already there
            words = json.loads(row["words_json"])
            if normalized not in words:
                words.append(normalized)
                cur.execute(
                    "UPDATE theme_word_lists SET words_json = ? WHERE id = ?;",
                    (json.dumps(words), row["id"])
                )
                logger.info(
                    "Palabra '%s' agregada al tema %d en dificultad %s",
                    normalized, theme_id, difficulty
                )


def delete_word(word_id: int) -> None:
    """Elimina una palabra del tema basado en el word_id fake."""
    # Parse word_id: list_id * 1000 + idx
    list_id = word_id // 1000
    idx = word_id % 1000

    # Get the word list
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT words_json FROM theme_word_lists WHERE id = ?;", (list_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"No existe la lista de palabras con id {list_id}.")
        words = json.loads(row["words_json"])
        if idx >= len(words):
            raise ValueError(f"Índice de palabra inválido: {idx}")
        # Remove the word
        words.pop(idx)
        # Update the list
        cur.execute(
            "UPDATE theme_word_lists SET words_json = ? WHERE id = ?;",
            (json.dumps(words), list_id)
        )
        logger.info("Palabra eliminada del tema, list_id %d, índice %d", list_id, idx)


# endregion
