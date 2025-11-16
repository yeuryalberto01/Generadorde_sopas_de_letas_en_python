import sqlite3
from contextlib import contextmanager
from pathlib import Path

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
        # Temas (futuro)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );
            """
        )
        # Palabras (futuro)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                FOREIGN KEY (theme_id) REFERENCES themes(id)
            );
            """
        )
        # Layouts de página (futuro)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS page_layouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                layout_json TEXT NOT NULL
            );
            """
        )
