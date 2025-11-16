from typing import List, Tuple, Optional
from pydantic import BaseModel


class PuzzleConfig(BaseModel):
    theme_id: Optional[int] = None
    words: List[str]
    rows: int = 15
    cols: int = 15
    difficulty: str = "medium"  # "easy" | "medium" | "hard"


class WordPosition(BaseModel):
    word: str
    start: Tuple[int, int]  # (fila, columna)
    end: Tuple[int, int]
    direction: str  # ej. "H", "V", "D+", "D-"


class PuzzleResult(BaseModel):
    grid: List[List[str]]
    positions: List[WordPosition]
