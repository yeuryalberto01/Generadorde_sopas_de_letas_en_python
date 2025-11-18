"""
Módulo de sugerencias inteligentes usando técnicas de similitud (ML básico).

Proporciona funciones para sugerir palabras relacionadas basadas en similitud
de strings y análisis de temas existentes.
"""

from __future__ import annotations

import difflib
import logging
from typing import List

from .themes import list_themes, get_theme

logger = logging.getLogger(__name__)


def suggest_similar_words(theme_id: int, limit: int = 5) -> List[str]:
    """
    Sugiere palabras similares para un tema basado en sus palabras existentes.

    Args:
        theme_id: ID del tema para el cual sugerir palabras.
        limit: Número máximo de sugerencias.

    Returns:
        Lista de palabras sugeridas ordenadas por similitud.
    """
    # Obtener el tema actual con sus palabras
    current_theme = get_theme(theme_id)
    if not current_theme:
        logger.warning("Tema con ID %d no encontrado", theme_id)
        return []

    # Obtener palabras del tema actual
    current_words = set()
    for word_list in current_theme.word_lists:
        current_words.update(word_list.words)

    if not current_words:
        logger.info("Tema '%s' no tiene palabras, no se pueden generar sugerencias", current_theme.name)
        return []

    # Obtener todos los temas para recopilar palabras de otros temas
    all_themes = list_themes()
    all_other_words = set()
    for theme_summary in all_themes:
        if theme_summary.id != theme_id:
            # Cargar el tema completo para obtener sus palabras
            full_theme = get_theme(theme_summary.id)
            if full_theme:
                for word_list in full_theme.word_lists:
                    all_other_words.update(word_list.words)

    # Calcular similitudes con palabras del tema actual
    similarities = []
    for current_word in current_words:
        for other_word in all_other_words:
            if other_word not in current_words:  # No sugerir palabras ya existentes
                ratio = difflib.SequenceMatcher(None, current_word, other_word).ratio()
                if ratio > 0.3:  # Umbral de similitud bajo para sugerencias de tema
                    similarities.append((other_word, ratio))

    # Eliminar duplicados y ordenar por similitud descendente
    unique_similarities = {}
    for word, ratio in similarities:
        if word not in unique_similarities or ratio > unique_similarities[word]:
            unique_similarities[word] = ratio

    sorted_suggestions = sorted(unique_similarities.items(), key=lambda x: x[1], reverse=True)
    suggestions = [w for w, _ in sorted_suggestions[:limit]]

    logger.info("Sugerencias para tema '%s' (ID %d): %s", current_theme.name, theme_id, suggestions)
    return suggestions


def analyze_theme_popularity() -> dict:
    """
    Analiza la popularidad de temas basada en el número de palabras.

    Returns:
        Diccionario con estadísticas de temas.
    """
    themes = list_themes()
    stats = {}
    for theme in themes:
        total_words = sum(len(wl.words) for wl in theme.word_lists)
        stats[theme.name] = {
            'id': theme.id,
            'total_words': total_words,
            'difficulties': len(theme.word_lists)
        }
    logger.info("Estadísticas de temas: %s", stats)
    return stats


def predict_difficulty(words: List[str]) -> str:
    """
    Predice la dificultad basada en la longitud promedio de las palabras.

    Args:
        words: Lista de palabras.

    Returns:
        Dificultad predicha: 'fácil', 'medio', 'difícil'.
    """
    if not words:
        return 'medio'

    avg_length = sum(len(w) for w in words) / len(words)
    if avg_length < 5:
        difficulty = 'fácil'
    elif avg_length < 8:
        difficulty = 'medio'
    else:
        difficulty = 'difícil'

    logger.info("Dificultad predicha para %d palabras (longitud avg %.1f): %s", len(words), avg_length, difficulty)
    return difficulty