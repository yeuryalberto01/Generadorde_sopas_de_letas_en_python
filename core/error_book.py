"""
Libro de Errores Inteligente - Sistema de depuración con ML.

Utiliza técnicas de similitud para clasificar errores, sugerir soluciones
y mejorar la depuración basándose en patrones de errores conocidos.
"""

from __future__ import annotations

import difflib
import logging
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorEntry:
    """Representa una entrada de error con metadatos."""

    def __init__(self, error_type: str, message: str, traceback_str: str = "",
                 context: Optional[Dict] = None):
        self.error_type = error_type
        self.message = message
        self.traceback = traceback_str
        self.context = context or {}
        self.timestamp = datetime.now()
        self.suggestions: List[str] = []
        self.similarity_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'error_type': self.error_type,
            'message': self.message,
            'traceback': self.traceback,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'suggestions': self.suggestions,
            'similarity_score': self.similarity_score
        }


class ErrorBook:
    """
    Sistema inteligente para manejo y análisis de errores.

    Utiliza similitud de strings para encontrar patrones de errores conocidos
    y proporcionar sugerencias automáticas de solución.
    """

    def __init__(self):
        self.known_errors: Dict[str, Dict] = self._load_known_errors()
        self.error_history: List[ErrorEntry] = []

    def _load_known_errors(self) -> Dict[str, Dict]:
        """Carga la base de conocimiento de errores conocidos con soluciones."""
        return {
            "ImportError": {
                "patterns": [
                    "cannot import name",
                    "No module named",
                    "ImportError"
                ],
                "solutions": [
                    "Verificar que el módulo esté instalado: pip install <module>",
                    "Revisar el PYTHONPATH",
                    "Verificar que el archivo __init__.py existe en el directorio del módulo"
                ]
            },
            "PuzzleGenerationError": {
                "patterns": [
                    "No se pudo generar puzzle",
                    "insufficient words",
                    "grid too small"
                ],
                "solutions": [
                    "Aumentar el número de palabras en el tema",
                    "Reducir el tamaño de la cuadrícula",
                    "Verificar que las palabras no sean demasiado largas"
                ]
            },
            "DatabaseError": {
                "patterns": [
                    "sqlite3",
                    "database",
                    "SQL"
                ],
                "solutions": [
                    "Verificar que la base de datos existe",
                    "Comprobar permisos de escritura",
                    "Revisar la integridad de la base de datos"
                ]
            },
            "FileNotFoundError": {
                "patterns": [
                    "No such file or directory",
                    "file not found"
                ],
                "solutions": [
                    "Verificar que la ruta del archivo es correcta",
                    "Crear directorios necesarios",
                    "Comprobar permisos de lectura"
                ]
            },
            "ValueError": {
                "patterns": [
                    "invalid literal",
                    "ValueError",
                    "could not convert"
                ],
                "solutions": [
                    "Verificar el tipo de datos esperado",
                    "Validar entrada del usuario",
                    "Usar try-except para conversiones"
                ]
            }
        }

    def capture_error(self, exc: Exception, context: Optional[Dict] = None) -> ErrorEntry:
        """
        Captura y analiza un error.

        Args:
            exc: La excepción capturada.
            context: Contexto adicional del error.

        Returns:
            ErrorEntry con análisis y sugerencias.
        """
        error_type = type(exc).__name__
        message = str(exc)
        traceback_str = traceback.format_exc()

        entry = ErrorEntry(error_type, message, traceback_str, context)

        # Analizar el error usando similitud
        suggestions, score = self._analyze_error(entry)
        entry.suggestions = suggestions
        entry.similarity_score = score

        # Agregar a historial
        self.error_history.append(entry)

        # Registrar en log con sugerencias
        self._log_error_with_suggestions(entry)

        return entry

    def _analyze_error(self, entry: ErrorEntry) -> Tuple[List[str], float]:
        """
        Analiza un error usando similitud con errores conocidos.

        Returns:
            Tupla de (sugerencias, puntuación de similitud máxima)
        """
        error_text = f"{entry.error_type}: {entry.message}"
        best_match = None
        max_score = 0.0

        for error_category, data in self.known_errors.items():
            for pattern in data["patterns"]:
                score = difflib.SequenceMatcher(None, error_text.lower(), pattern.lower()).ratio()
                if score > max_score:
                    max_score = score
                    best_match = data["solutions"]

        if best_match and max_score > 0.3:  # Umbral de similitud
            return best_match, max_score

        # Sugerencias genéricas si no hay coincidencia
        return [
            "Revisar el código fuente donde ocurre el error",
            "Verificar logs adicionales para más contexto",
            "Consultar documentación del framework utilizado"
        ], 0.0

    def _log_error_with_suggestions(self, entry: ErrorEntry) -> None:
        """Registra el error en el log con sugerencias."""
        logger.error(
            "ERROR CAPTURADO [%s]: %s - %s",
            entry.error_type,
            entry.message,
            " | ".join(entry.suggestions[:2])  # Mostrar primeras 2 sugerencias
        )

        if entry.traceback:
            logger.debug("Traceback completo:\n%s", entry.traceback)

        if entry.context:
            logger.debug("Contexto del error: %s", entry.context)

    def get_error_statistics(self) -> Dict:
        """Obtiene estadísticas de errores."""
        if not self.error_history:
            return {"total_errors": 0}

        error_types = {}
        for entry in self.error_history:
            error_types[entry.error_type] = error_types.get(entry.error_type, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "most_common": max(error_types.items(), key=lambda x: x[1]) if error_types else None,
            "recent_errors": [e.to_dict() for e in self.error_history[-5:]]
        }

    def suggest_improvements(self) -> List[str]:
        """Sugiere mejoras basadas en patrones de errores."""
        stats = self.get_error_statistics()
        suggestions = []

        if stats["total_errors"] > 10:
            suggestions.append("Considerar agregar más validaciones de entrada")
        if "ImportError" in stats.get("error_types", {}):
            suggestions.append("Revisar dependencias del proyecto")
        if "PuzzleGenerationError" in stats.get("error_types", {}):
            suggestions.append("Optimizar algoritmo de generación de puzzles")

        return suggestions

    def clear_history(self) -> None:
        """Limpia el historial de errores."""
        self.error_history.clear()
        logger.info("Historial de errores limpiado")


# Instancia global del libro de errores
error_book = ErrorBook()


def capture_exception(exc: Exception, context: Optional[Dict] = None) -> ErrorEntry:
    """
    Función de conveniencia para capturar errores.

    Args:
        exc: La excepción a capturar.
        context: Contexto adicional.

    Returns:
        La entrada de error creada.
    """
    return error_book.capture_error(exc, context)


def get_error_stats() -> Dict:
    """Obtiene estadísticas de errores."""
    return error_book.get_error_statistics()


def get_improvement_suggestions() -> List[str]:
    """Obtiene sugerencias de mejora."""
    return error_book.suggest_improvements()