from __future__ import annotations

import random
from typing import Dict, Iterable, List, Tuple

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - fallback para usuarios sin dependencias
    raise ImportError(
        "numpy es requerido para generar las sopas. Instala dependencias con "
        "`pip install -r requirements.txt`."
    ) from exc

from .models import PuzzleConfig, PuzzleResult, WordPosition

DirectionVec = Tuple[int, int]

# Direcciones cardinales y diagonales admitidas
DIRECTIONS: Dict[str, DirectionVec] = {
    "E": (0, 1),
    "W": (0, -1),
    "S": (1, 0),
    "N": (-1, 0),
    "SE": (1, 1),
    "SW": (1, -1),
    "NE": (-1, 1),
    "NW": (-1, -1),
}

MAX_ATTEMPTS_PER_WORD = 200


class PuzzleGenerationError(RuntimeError):
    """Se lanza cuando no es posible colocar una palabra en la grilla."""


def generate_puzzle(config: PuzzleConfig) -> PuzzleResult:
    """Genera una sopa de letras respetando la configuración proporcionada."""

    rows, cols = config.rows, config.cols
    grid = np.full((rows, cols), "", dtype="<U1")
    rng = random.Random()
    positions: list[WordPosition] = []

    ordered_words = sorted(config.words, key=len, reverse=True)
    allowed_dirs = _resolve_directions(config.directions)

    for word in ordered_words:
        placed = _place_word(word, grid, allowed_dirs, rng)
        if placed is None:
            raise PuzzleGenerationError(f"No fue posible colocar la palabra '{word}'.")
        positions.append(WordPosition(word=word, start=placed[0], end=placed[1], direction=placed[2]))

    _fill_empty_cells(grid, rng, config.alphabet)
    return PuzzleResult(grid=grid.tolist(), positions=positions)


def _resolve_directions(direction_names: Iterable[str]) -> List[Tuple[str, DirectionVec]]:
    resolved: list[tuple[str, DirectionVec]] = []
    for name in direction_names:
        vec = DIRECTIONS.get(name)
        if vec is None:
            raise ValueError(f"Dirección no reconocida: {name}")
        resolved.append((name, vec))
    return resolved


def _place_word(
    word: str,
    grid: np.ndarray,
    directions: List[Tuple[str, DirectionVec]],
    rng: random.Random,
) -> Tuple[Tuple[int, int], Tuple[int, int], str] | None:
    rows, cols = grid.shape
    word_len = len(word)
    attempts = 0

    while attempts < MAX_ATTEMPTS_PER_WORD:
        direction_name, (dr, dc) = rng.choice(directions)
        start_row, end_row = _start_bounds(rows, dr, word_len)
        start_col, end_col = _start_bounds(cols, dc, word_len)

        row = rng.randint(start_row, end_row)
        col = rng.randint(start_col, end_col)

        if _fits(word, row, col, dr, dc, grid):
            _commit_word(word, row, col, dr, dc, grid)
            end_pos = (row + dr * (word_len - 1), col + dc * (word_len - 1))
            return (row, col), end_pos, direction_name

        attempts += 1
    return None


def _start_bounds(limit: int, delta: int, word_len: int) -> Tuple[int, int]:
    if delta == 0:
        return 0, limit - 1
    if delta > 0:
        return 0, limit - word_len
    return word_len - 1, limit - 1


def _fits(
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
    grid: np.ndarray,
) -> bool:
    rows, cols = grid.shape
    for letter in word:
        if row < 0 or row >= rows or col < 0 or col >= cols:
            return False
        existing = grid[row, col]
        if existing and existing != letter:
            return False
        row += dr
        col += dc
    return True


def _commit_word(
    word: str,
    row: int,
    col: int,
    dr: int,
    dc: int,
    grid: np.ndarray,
) -> None:
    for letter in word:
        grid[row, col] = letter
        row += dr
        col += dc


def _fill_empty_cells(grid: np.ndarray, rng: random.Random, alphabet: str) -> None:
    mask = grid == ""
    empties = np.argwhere(mask)
    for row, col in empties:
        grid[row, col] = rng.choice(alphabet)
