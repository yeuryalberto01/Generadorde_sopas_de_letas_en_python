"""Normalización y validación de palabras para sopas de letras."""

from __future__ import annotations

import re
import unicodedata
from typing import List, Optional

from pydantic import BaseModel

from .config import load_config

ALLOWED_CHARS_PATTERN = re.compile(r"^[A-ZÑ]+$")
REPLACEMENTS = str.maketrans(
    {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
    }
)


class WordValidationResult(BaseModel):
    valid: bool
    normalized: str
    original: str
    errors: List[str]


def _normalize_text(value: str) -> str:
    text = value.strip().upper()
    # Mantener Ñ manualmente
    normalized_chars: list[str] = []
    for char in text:
        if char == "Ñ":
            normalized_chars.append(char)
            continue
        normalized_chars.append(char.translate(REPLACEMENTS))
    joined = "".join(normalized_chars)
    # Eliminar diacríticos residuales
    decomposed = unicodedata.normalize("NFD", joined)
    cleaned = "".join(c for c in decomposed if not unicodedata.combining(c))
    return cleaned


def validate_word(raw: str, config: Optional[dict] = None) -> WordValidationResult:
    """Normaliza y valida una palabra según las reglas configuradas."""
    original = raw
    text = raw.strip()
    errors: list[str] = []
    if not text:
        errors.append("Palabra vacía.")
        return WordValidationResult(valid=False, normalized="", original=original, errors=errors)

    cfg = config or load_config()
    words_cfg = cfg.get("words", {})
    min_len = max(1, int(words_cfg.get("min_length", 1)))
    max_len = int(words_cfg.get("max_length", 100))

    normalized = _normalize_text(text)

    length = len(normalized)
    if length < min_len:
        errors.append(f"La palabra debe tener al menos {min_len} caracteres.")
    if length > max_len:
        errors.append(f"La palabra no puede exceder {max_len} caracteres.")

    if normalized and not ALLOWED_CHARS_PATTERN.match(normalized):
        errors.append("Caracteres inválidos. Solo se permiten letras A-Z o Ñ.")

    is_valid = not errors
    return WordValidationResult(
        valid=is_valid,
        normalized=normalized if is_valid else "",
        original=original,
        errors=errors,
    )


__all__ = ["WordValidationResult", "validate_word"]
