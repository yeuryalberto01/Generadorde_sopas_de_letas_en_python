"""Diálogo ligero para generar una sopa en pocos pasos."""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QComboBox,
)

from core import load_config
from core.models import PuzzleConfig


class QuickGeneratorDialog(QDialog):
    """Interfaz compacta enfocada en la lista de palabras y el tamaño."""

    def __init__(
        self,
        parent=None,
        *,
        preset_words: Iterable[str] | None = None,
        default_rows: int | None = None,
        default_cols: int | None = None,
        default_difficulty: str | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Generador rápido")
        self.resize(420, 460)
        self._app_cfg = load_config()
        grid_defaults = self._app_cfg.get("grid", {}).get("default_size", (15, 15))
        self._default_rows = default_rows or grid_defaults[0]
        self._default_cols = default_cols or grid_defaults[1]
        self._default_difficulty = (default_difficulty or "medio").lower()

        self._build_ui(preset_words)

    def _build_ui(self, preset_words: Iterable[str] | None) -> None:
        layout = QVBoxLayout(self)
        description = QLabel(
            "Pega o escribe tus palabras (una por línea) y deja que el generador\n"
            "complete el resto con la configuración predeterminada.",
            self,
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()

        self.rows_spin = QSpinBox(self)
        self.rows_spin.setRange(PuzzleConfig.MIN_SIZE, PuzzleConfig.MAX_SIZE)
        self.rows_spin.setValue(self._default_rows)
        form.addRow("Filas", self.rows_spin)

        self.cols_spin = QSpinBox(self)
        self.cols_spin.setRange(PuzzleConfig.MIN_SIZE, PuzzleConfig.MAX_SIZE)
        self.cols_spin.setValue(self._default_cols)
        form.addRow("Columnas", self.cols_spin)

        self.difficulty_combo = QComboBox(self)
        for diff in sorted(PuzzleConfig.ALLOWED_DIFFICULTIES):
            self.difficulty_combo.addItem(diff.capitalize(), diff)
        default_index = self.difficulty_combo.findData(self._default_difficulty)
        if default_index >= 0:
            self.difficulty_combo.setCurrentIndex(default_index)
        form.addRow("Dificultad", self.difficulty_combo)

        layout.addLayout(form)

        words_label = QLabel("Palabras", self)
        layout.addWidget(words_label)
        self.words_input = QPlainTextEdit(self)
        self.words_input.setPlaceholderText("python\nqt\nwidget\npuzzle\n...")
        if preset_words:
            prepared = "\n".join(word.strip() for word in preset_words if word.strip())
            self.words_input.setPlainText(prepared)
        layout.addWidget(self.words_input, stretch=1)

        self.persist_checkbox = QCheckBox("Guardar automáticamente después de generar", self)
        self.persist_checkbox.setChecked(True)
        layout.addWidget(self.persist_checkbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def word_list(self) -> list[str]:
        return [
            line.strip()
            for line in self.words_input.toPlainText().splitlines()
            if line.strip()
        ]

    def should_persist(self) -> bool:
        return self.persist_checkbox.isChecked()

    def build_config(self) -> PuzzleConfig:
        data = {
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
            "difficulty": self.difficulty_combo.currentData(),
            "words": self.word_list(),
        }
        return PuzzleConfig(**data)


__all__ = ["QuickGeneratorDialog"]
