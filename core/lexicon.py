"""Normalización y validación de palabras para sopas de letras."""

from __future__ import annotations

import re
import unicodedata
from typing import List

from pydantic import BaseModel

from .config import load_config

ALLOWED_CHARS_PATTERN = re.compile(r"^[A-ZÑ]+$")


class WordValidationResult(BaseModel):
    valid: bool
    normalized: str
    errors: List[str]


def _strip_accents(text: str) -> str:
    cleaned_chars: list[str] = []
    for char in text:
        if char.lower() == "ñ":
            cleaned_chars.append("Ñ")
            continue
        decomposed = unicodedata.normalize("NFD", char)
        base = "".join(c for c in decomposed if not unicodedata.combining(c))
        cleaned_chars.append(base)
    return "".join(cleaned_chars)


def validate_word(raw: str) -> WordValidationResult:
    """Normaliza y valida una palabra según las reglas configuradas."""
    errors: list[str] = []
    cfg = load_config()
    words_cfg = cfg.get("words", {})
    min_len = max(1, int(words_cfg.get("min_length", 2)))
    max_len = int(words_cfg.get("max_length", 30))

    stripped = raw.strip()
    if not stripped:
        errors.append("La palabra está vacía.")
        return WordValidationResult(valid=False, normalized="", errors=errors)

    normalized = _strip_accents(stripped).upper()

    if len(normalized) < min_len:
        errors.append(f"La palabra debe tener al menos {min_len} caracteres.")
    if len(normalized) > max_len:
        errors.append(f"La palabra no puede exceder {max_len} caracteres.")

    if normalized and not ALLOWED_CHARS_PATTERN.match(normalized):
        errors.append("Solo se permiten letras A-Z o Ñ.")

    is_valid = not errors
    return WordValidationResult(valid=is_valid, normalized=normalized if is_valid else "", errors=errors)


__all__ = ["WordValidationResult", "validate_word"]
