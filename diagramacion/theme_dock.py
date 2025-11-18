"""Dock para selección de temas y dificultades."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QComboBox,
    QDockWidget,
    QGroupBox,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QPushButton,
    QMainWindow,
)
from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module

from core import themes
from core.models import Theme


class ThemeSelectionDock(QDockWidget):
    """Dock para seleccionar categoría, tema y dificultad."""

    def __init__(self, main_window: QMainWindow, parent=None):
        super().__init__("Selección de Tema", parent)
        self.main_window = main_window
        self._selected_theme: Optional[Theme] = None
        self._selected_difficulty: Optional[str] = None

        self.category_combo = QComboBox(self)
        self.category_combo.addItem("Todas las Categorías", None)
        self.category_combo.currentIndexChanged.connect(self._handle_category_selection)

        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Seleccionar Tema", None)
        self.theme_combo.currentIndexChanged.connect(self._handle_theme_selection)

        self.difficulty_combo = QComboBox(self)
        self.difficulty_combo.addItem("Seleccionar Dificultad", None)
        self.difficulty_combo.currentIndexChanged.connect(self._update_selected_difficulty)

        self._build_ui()
        self.load_categories()

    def _build_ui(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Categoría
        category_group = QGroupBox("Categoría")
        category_layout = QVBoxLayout(category_group)
        category_layout.addWidget(self.category_combo)
        layout.addWidget(category_group)

        # Tema
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)

        # Dificultad
        difficulty_group = QGroupBox("Dificultad")
        difficulty_layout = QVBoxLayout(difficulty_group)
        difficulty_layout.addWidget(self.difficulty_combo)
        layout.addWidget(difficulty_group)

        # Botones
        self.btn_generate_from_theme = QPushButton("Generar desde Tema", self)
        self.btn_generate_from_theme.clicked.connect(self._handle_generate_from_selected_theme)
        layout.addWidget(self.btn_generate_from_theme)

        self.btn_manage_themes = QPushButton("Gestionar Temas", self)
        self.btn_manage_themes.clicked.connect(self._handle_manage_themes)
        layout.addWidget(self.btn_manage_themes)

        layout.addStretch()
        self.setWidget(widget)

    def load_categories(self) -> None:
        try:
            categories = themes.list_categories()
            for cat in categories:
                self.category_combo.addItem(cat.name, cat.id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            QMessageBox.critical(self, "Error", f"Error al cargar categorías: {exc}")
        self._load_themes()

    def _handle_category_selection(self) -> None:
        self._load_themes()

    def _load_themes(self) -> None:
        self.theme_combo.clear()
        self.theme_combo.addItem("Seleccionar Tema", None)
        self._selected_theme = None

        selected_category_id = self.category_combo.currentData()
        try:
            all_themes = themes.list_themes()
            filtered_themes = [
                t for t in all_themes
                if selected_category_id is None or (t.category and t.category.id == selected_category_id)
            ]
            for t in filtered_themes:
                self.theme_combo.addItem(t.name, t.id)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            QMessageBox.critical(self, "Error", f"Error al cargar temas: {exc}")
        self._load_difficulties()

    def _handle_theme_selection(self) -> None:
        theme_id = self.theme_combo.currentData()
        if theme_id is not None:
            try:
                self._selected_theme = themes.get_theme(theme_id)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                QMessageBox.critical(self, "Error", f"Error al cargar el tema: {exc}")
                self._selected_theme = None
        else:
            self._selected_theme = None
        self._load_difficulties()

    def _load_difficulties(self) -> None:
        self.difficulty_combo.clear()
        self.difficulty_combo.addItem("Seleccionar Dificultad", None)
        self._selected_difficulty = None

        if self._selected_theme and self._selected_theme.word_lists:  # type: ignore
            for wl in self._selected_theme.word_lists:  # type: ignore
                self.difficulty_combo.addItem(wl.difficulty.capitalize(), wl.difficulty)

        # Seleccionar dificultad por defecto
        if self._selected_theme and self._selected_theme.metadata:  # type: ignore
            default_difficulty = self._selected_theme.metadata.get("default_difficulty")  # type: ignore
            if default_difficulty:
                index = self.difficulty_combo.findData(default_difficulty.lower())
                if index != -1:
                    self.difficulty_combo.setCurrentIndex(index)
                    self._selected_difficulty = default_difficulty.lower()

    def _update_selected_difficulty(self) -> None:
        self._selected_difficulty = self.difficulty_combo.currentData()

    def get_selected_theme_and_difficulty(self) -> tuple[Optional[Theme], Optional[str]]:
        return self._selected_theme, self._selected_difficulty

    def _handle_generate_from_selected_theme(self) -> None:
        self.main_window._handle_generate_from_selected_theme()  # pylint: disable=protected-access

    def _handle_manage_themes(self) -> None:
        self.main_window.open_temas_module()