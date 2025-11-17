"""Diálogo para capturar la configuración de un nuevo puzzle."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
)

from core import load_config
from core.models import PuzzleConfig


class ConfigDialog(QDialog):
    """Diálogo modal que permite definir palabras y dimensiones del puzzle."""

    def __init__(self, parent=None, base_config: PuzzleConfig | None = None):
        super().__init__(parent)
        self.setWindowTitle("Configurar nuevo puzzle")
        self.resize(520, 560)
        self._app_cfg = load_config()
        self._base = base_config
        self._build_ui()
        if base_config is not None:
            self._apply_from_config(base_config)

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        default_rows, default_cols = self._app_cfg.get("grid", {}).get("default_size", (15, 15))
        self.rows_spin = QSpinBox(self)
        self.rows_spin.setRange(PuzzleConfig.MIN_SIZE, PuzzleConfig.MAX_SIZE)
        self.rows_spin.setValue(default_rows)
        form_layout.addRow("Filas", self.rows_spin)

        self.cols_spin = QSpinBox(self)
        self.cols_spin.setRange(PuzzleConfig.MIN_SIZE, PuzzleConfig.MAX_SIZE)
        self.cols_spin.setValue(default_cols)
        form_layout.addRow("Columnas", self.cols_spin)

        self.difficulty_combo = QComboBox(self)
        for diff in sorted(PuzzleConfig.ALLOWED_DIFFICULTIES):
            self.difficulty_combo.addItem(diff.capitalize(), diff)
        self.difficulty_combo.setCurrentText("Medio")
        form_layout.addRow("Dificultad", self.difficulty_combo)

        self.alphabet_input = QLineEdit(self)
        self.alphabet_input.setPlaceholderText("Alfabeto personalizado (opcional)")
        form_layout.addRow("Alfabeto", self.alphabet_input)

        directions_box = QGroupBox("Direcciones permitidas", self)
        directions_layout = QVBoxLayout(directions_box)
        self.direction_list = QListWidget(self)
        self.direction_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for direction in PuzzleConfig.DEFAULT_DIRECTIONS:
            item = QListWidgetItem(direction)
            item.setSelected(True)
            self.direction_list.addItem(item)
        directions_layout.addWidget(self.direction_list)

        words_box = QGroupBox("Palabras", self)
        words_layout = QVBoxLayout(words_box)
        words_layout.addWidget(
            QLabel("Ingresa una palabra por línea. Se ignoran espacios en blanco.", self)
        )
        self.words_input = QPlainTextEdit(self)
        self.words_input.setPlaceholderText("python\nqt\ninterface\neditor\n...")
        words_layout.addWidget(self.words_input)

        options_widget = QGroupBox("Opciones adicionales", self)
        options_layout = QGridLayout(options_widget)
        self.persist_checkbox = QCheckBox("Guardar en la base de datos al generar", self)
        self.persist_checkbox.setChecked(True)
        options_layout.addWidget(self.persist_checkbox, 0, 0, 1, 2)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(directions_box)
        main_layout.addWidget(words_box)
        main_layout.addWidget(options_widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _apply_from_config(self, config: PuzzleConfig) -> None:
        self.rows_spin.setValue(config.rows)
        self.cols_spin.setValue(config.cols)
        index = self.difficulty_combo.findData(config.difficulty)
        if index >= 0:
            self.difficulty_combo.setCurrentIndex(index)
        self.alphabet_input.setText(config.alphabet)
        existing_dirs = set(config.directions)
        for idx in range(self.direction_list.count()):
            item = self.direction_list.item(idx)
            item.setSelected(item.text() in existing_dirs)
        self.words_input.setPlainText("\n".join(config.words))

    def selected_directions(self) -> List[str]:
        selected = [item.text() for item in self.direction_list.selectedItems()]
        return selected or PuzzleConfig.DEFAULT_DIRECTIONS.copy()

    def word_list(self) -> List[str]:
        return [line.strip() for line in self.words_input.toPlainText().splitlines() if line.strip()]

    def should_persist(self) -> bool:
        return self.persist_checkbox.isChecked()

    def build_config(self) -> PuzzleConfig:
        data = {
            "rows": self.rows_spin.value(),
            "cols": self.cols_spin.value(),
            "difficulty": self.difficulty_combo.currentData(),
            "words": self.word_list(),
            "directions": self.selected_directions(),
        }
        if alphabet_text := self.alphabet_input.text().strip():
            data["alphabet"] = alphabet_text
        return PuzzleConfig(**data)


def show_validation_error(parent, message: str) -> None:
    QMessageBox.critical(parent, "Configuración inválida", message)


__all__ = ["ConfigDialog", "show_validation_error"]
