from __future__ import annotations

from typing import ClassVar, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator, model_validator

from .lexicon import validate_word

DEFAULT_DIRECTION_SET = [
    "E",
    "W",
    "N",
    "S",
    "NE",
    "NW",
    "SE",
    "SW",
]


class PuzzleConfig(BaseModel):
    """Configuración canónica para generar una sopa de letras."""

    MIN_SIZE: ClassVar[int] = 5
    MAX_SIZE: ClassVar[int] = 35
    MIN_ALPHABET_LENGTH: ClassVar[int] = 2
    ALLOWED_DIFFICULTIES: ClassVar[set[str]] = {"easy", "medium", "hard"}
    DEFAULT_DIRECTIONS: ClassVar[list[str]] = DEFAULT_DIRECTION_SET

    theme_id: Optional[int] = None
    words: List[str] = Field(min_length=1)
    rows: int = Field(default=15)
    cols: int = Field(default=15)
    difficulty: str = Field(default="medium")
    alphabet: str = Field(
        default="ABCDEFGHIJKLMNÑOPQRSTUVWXYZ", min_length=MIN_ALPHABET_LENGTH
    )
    directions: List[str] = Field(default_factory=lambda: DEFAULT_DIRECTION_SET.copy())

    @field_validator("rows", "cols")
    @classmethod
    def _check_size(cls, value: int) -> int:
        if not cls.MIN_SIZE <= value <= cls.MAX_SIZE:
            raise ValueError(
                f"Las dimensiones deben estar entre {cls.MIN_SIZE} y {cls.MAX_SIZE}"
            )
        return value

    @field_validator("difficulty")
    @classmethod
    def _check_difficulty(cls, value: str) -> str:
        value = value.lower()
        if value not in cls.ALLOWED_DIFFICULTIES:
            raise ValueError(f"Dificultad inválida: {value}")
        return value

    @field_validator("alphabet")
    @classmethod
    def _normalize_alphabet(cls, value: str) -> str:
        normalized_chars: list[str] = []
        seen: set[str] = set()
        for char in value:
            upper = char.upper()
            if not upper.strip() or upper in seen:
                continue
            seen.add(upper)
            normalized_chars.append(upper)
        normalized = "".join(normalized_chars)
        if len(normalized) < cls.MIN_ALPHABET_LENGTH:
            raise ValueError("El alfabeto debe tener al menos 2 caracteres distintos.")
        return normalized

    @field_validator("directions")
    @classmethod
    def _validate_directions(cls, directions: List[str]) -> List[str]:
        valid = set(cls.DEFAULT_DIRECTIONS)
        cleaned = []
        for direction in directions:
            direction = direction.upper()
            if direction not in valid:
                raise ValueError(f"Dirección no soportada: {direction}")
            if direction not in cleaned:
                cleaned.append(direction)
        if not cleaned:
            raise ValueError("Debe proporcionar al menos una dirección para colocar palabras.")
        return cleaned

    @field_validator("words")
    @classmethod
    def _normalize_words(cls, words: List[str]) -> List[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for word in words:
            result = validate_word(word)
            if not result.valid:
                raise ValueError("; ".join(result.errors))
            clean = result.normalized
            if clean in seen:
                raise ValueError(f"La palabra '{clean}' está duplicada.")
            normalized.append(clean)
            seen.add(clean)
        if not normalized:
            raise ValueError("Debe proporcionar al menos una palabra válida.")
        return normalized

    @model_validator(mode="after")
    def _words_fit_grid(self) -> "PuzzleConfig":
        longest = max(len(word) for word in self.words)
        longest_axis = max(self.rows, self.cols)
        if longest > longest_axis:
            raise ValueError(
                f"La palabra más larga ({longest}) no cabe en la grilla {self.rows}x{self.cols}."
            )
        return self


class WordPosition(BaseModel):
    word: str
    start: Tuple[int, int]  # (fila, columna)
    end: Tuple[int, int]
    direction: str  # ej. "E", "SW", etc.


class PuzzleResult(BaseModel):
    grid: List[List[str]]
    positions: List[WordPosition]
