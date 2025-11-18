"""Controlador para la lógica de generación y manejo de puzzles."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QMessageBox  # pylint: disable=no-name-in-module

from core import (
    PuzzleGenerationError,
    generate_puzzle,
    load_config,
    load_puzzle,
    save_puzzle,
)
from core.error_book import capture_exception
from core.models import PuzzleConfig, PuzzleResult, Theme


class PuzzleController:
    """Maneja la generación, carga y guardado de puzzles."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.current_config: Optional[PuzzleConfig] = None
        self.current_result: Optional[PuzzleResult] = None
        self._last_config_id: Optional[int] = None

    def generate_from_config(self, config: PuzzleConfig, persist: bool = False) -> bool:
        """Genera un puzzle desde una configuración."""
        try:
            result = generate_puzzle(config)
        except PuzzleGenerationError as exc:
            capture_exception(exc, {"context": "puzzle_generation", "config": config.__dict__})
            QMessageBox.warning(self.main_window, "No se pudo generar", str(exc))
            return False
        except Exception as exc:  # pylint: disable=broad-exception-caught
            capture_exception(exc, {
                "context": "puzzle_generation_unexpected",
                "config": config.__dict__
            })
            QMessageBox.critical(self.main_window, "Error inesperado", str(exc))
            return False

        config_id = None
        if persist:
            try:
                config_id = save_puzzle(config, result)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                capture_exception(exc, {"context": "puzzle_save", "config_id": config_id})
                QMessageBox.warning(
                    self.main_window,
                    "Persistencia fallida",
                    f"El puzzle se generó correctamente, pero no se pudo guardar:\n{exc}",
                )

        self.current_config = config
        self.current_result = result
        self.main_window.open_diagramacion_module()
        self.main_window.scene.display_puzzle(config, result)

        if config_id:
            self._last_config_id = config_id
            self.main_window.statusBar().showMessage(f"Puzzle guardado con ID {config_id}.", 5000)
        else:
            self.main_window.statusBar().showMessage("Puzzle generado.", 5000)

        return True

    def regenerate_last(self) -> bool:
        """Regenera el último puzzle."""
        if self.current_config is None:
            QMessageBox.information(
                self.main_window,
                "Sin configuraciones",
                "Genera primero un puzzle para poder regenerarlo.",
            )
            return False
        return self.generate_from_config(self.current_config, persist=True)

    def load_saved_puzzle(self, config_id: int) -> bool:
        """Carga un puzzle guardado."""
        try:
            config, result = load_puzzle(config_id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            QMessageBox.critical(self.main_window, "Error al abrir", str(exc))
            return False

        self.current_config = config
        self.current_result = result
        self._last_config_id = config_id
        self.main_window.scene.display_puzzle(config, result)
        self.main_window.statusBar().showMessage(
            f"Puzzle {config_id} cargado desde la base de datos.", 5000
        )
        return True

    def generate_from_theme(self, theme: Theme, difficulty: str) -> bool:
        """Genera un puzzle desde un tema y dificultad."""
        try:
            config = self.create_config_from_theme(theme, difficulty)
            return self.generate_from_config(config, persist=True)
        except ValueError as exc:
            QMessageBox.warning(self.main_window, "Error de Configuración", str(exc))
            return False
        except Exception as exc:  # pylint: disable=broad-exception-caught
            QMessageBox.critical(self.main_window, "Error", f"Error al generar desde tema: {exc}")
            return False

    def create_config_from_theme(self, theme: Theme, difficulty: str) -> PuzzleConfig:
        """Crea una configuración de puzzle desde un tema."""
        word_list_for_difficulty = next(
            (wl for wl in theme.word_lists if wl.difficulty == difficulty),
            None,
        )
        if not word_list_for_difficulty or not word_list_for_difficulty.words:
            raise ValueError(
                f"El tema '{theme.name}' no tiene palabras para la dificultad '{difficulty}'."
            )

        words = word_list_for_difficulty.words

        cfg = load_config()
        default_rows, default_cols = cfg.get("grid", {}).get(
            "default_size", (15, 15)
        )

        rows = theme.metadata.get("default_rows", default_rows)
        cols = theme.metadata.get("default_cols", default_cols)
        alphabet = theme.metadata.get(
            "default_alphabet", cfg.get("alphabet", "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ")
        )
        directions = theme.metadata.get("default_directions", PuzzleConfig.DEFAULT_DIRECTIONS)

        return PuzzleConfig(
            theme_id=theme.id,
            words=words,
            rows=rows,
            cols=cols,
            difficulty=difficulty,
            alphabet=alphabet,
            directions=directions,
        )

    def has_current_puzzle(self) -> bool:
        """Verifica si hay un puzzle actual."""
        return self.current_result is not None

    def get_current_result(self) -> Optional[PuzzleResult]:
        """Obtiene el resultado del puzzle actual."""
        return self.current_result
