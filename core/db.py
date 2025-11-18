import json
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import List, Tuple

from .models import PuzzleConfig, PuzzleResult, WordPosition

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "puzzles.db"


@contextmanager
def get_conn():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        # --- Nuevo Esquema de Temas ---

        # 1. Tabla para Categorías de Temas
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """
        )

        # 2. Tabla de Temas mejorada
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                category_id INTEGER,
                metadata_json TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
            """
        )

        # 3. Listas de palabras por Tema y Dificultad
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS theme_word_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                words_json TEXT NOT NULL,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
                UNIQUE (theme_id, difficulty)
            );
            """
        )

        # --- Fin del Nuevo Esquema de Temas ---

        # Layouts de página (sin cambios)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS page_layouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                layout_json TEXT NOT NULL
            );
            """
        )
        # Configuraciones utilizadas (sin cambios)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzle_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id INTEGER,
                rows INTEGER NOT NULL,
                cols INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                words_json TEXT NOT NULL,
                alphabet TEXT NOT NULL,
                directions_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Resultados generados (sin cambios)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzle_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id INTEGER NOT NULL,
                grid_json TEXT NOT NULL,
                positions_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (config_id) REFERENCES puzzle_configs(id)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_config_id ON puzzle_results(config_id);"
        )

        # Limpieza: Eliminar la tabla 'words' si existe, ya que es obsoleta
        cur.execute("DROP TABLE IF EXISTS words;")


def save_puzzle(config: PuzzleConfig, result: PuzzleResult) -> int:
    """Persiste una configuración y su resultado, devolviendo el ID de la config."""
    payload_config = {
        "theme_id": config.theme_id,
        "rows": config.rows,
        "cols": config.cols,
        "difficulty": config.difficulty,
        "words_json": json.dumps(config.words, ensure_ascii=False),
        "alphabet": config.alphabet,
        "directions_json": json.dumps(config.directions, ensure_ascii=False),
    }
    payload_result = {
        "grid_json": json.dumps(result.grid, ensure_ascii=False),
        "positions_json": json.dumps(
            [position.model_dump() for position in result.positions],
            ensure_ascii=False,
        ),
    }

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO puzzle_configs (theme_id, rows, cols, difficulty, words_json, alphabet, directions_json, created_at)
            VALUES (:theme_id, :rows, :cols, :difficulty, :words_json, :alphabet, :directions_json, :created_at)
            """,
            {**payload_config, "created_at": datetime.utcnow().isoformat()},
        )
        config_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO puzzle_results (config_id, grid_json, positions_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                config_id,
                payload_result["grid_json"],
                payload_result["positions_json"],
                datetime.utcnow().isoformat(),
            ),
        )
    return config_id


def load_puzzle(config_id: int) -> Tuple[PuzzleConfig, PuzzleResult]:
    """Carga una configuración y su resultado asociados al ID proporcionado."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, theme_id, rows, cols, difficulty, words_json, alphabet, directions_json
            FROM puzzle_configs
            WHERE id = ?
            """,
            (config_id,),
        )
        config_row = cur.fetchone()
        if config_row is None:
            raise ValueError(f"No existe el puzzle con id {config_id}")

        cur.execute(
            """
            SELECT grid_json, positions_json
            FROM puzzle_results
            WHERE config_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (config_id,),
        )
        result_row = cur.fetchone()
        if result_row is None:
            raise ValueError(f"No hay resultados para el puzzle con id {config_id}")

    _, theme_id, rows, cols, difficulty, words_json, alphabet, directions_json = config_row
    grid_json, positions_json = result_row

    config = PuzzleConfig(
        theme_id=theme_id,
        rows=rows,
        cols=cols,
        difficulty=difficulty,
        words=json.loads(words_json),
        alphabet=alphabet,
        directions=json.loads(directions_json),
    )
    positions = [WordPosition(**item) for item in json.loads(positions_json)]
    result = PuzzleResult(grid=json.loads(grid_json), positions=positions)
    return config, result


def list_recent_puzzles(limit: int = 10) -> List[Tuple[int, str, int, int, str]]:
    """Devuelve los puzzles guardados recientemente."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, difficulty, rows, cols, created_at
            FROM puzzle_configs
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()
