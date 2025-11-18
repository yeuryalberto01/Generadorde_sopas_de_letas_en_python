"""Diálogo para gestionar temas y palabras."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core import themes, suggest_similar_words

logger = logging.getLogger(__name__)


class TemasDialog(QDialog):
    """Permite crear/editar temas y administrar las palabras asociadas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Temas")
        self.resize(900, 520)
        self._theme_id: int | None = None
        self._themes_cache: list = []
        self._build_ui()
        self._load_themes()

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)

        # Columna izquierda: creación rápida de temas
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Nuevo tema", self))
        theme_form = QFormLayout()
        self.new_theme_name = QLineEdit(self)
        self.new_theme_desc = QLineEdit(self)
        self.new_theme_desc.setPlaceholderText("Descripción (opcional)")
        self.new_theme_desc.returnPressed.connect(self._handle_submit_theme)
        self.new_theme_name.returnPressed.connect(self._handle_submit_theme)
        theme_form.addRow("Nombre", self.new_theme_name)
        theme_form.addRow("Descripción", self.new_theme_desc)
        left_panel.addLayout(theme_form)

        btn_new_theme = QPushButton("Limpiar formulario", self)
        btn_new_theme.setDefault(False)
        btn_new_theme.clicked.connect(self._handle_new_theme_form)

        btn_add_theme = QPushButton("Crear tema", self)
        btn_add_theme.setDefault(False)
        btn_add_theme.clicked.connect(self._handle_add_theme)
        left_panel.addWidget(btn_new_theme)
        left_panel.addWidget(btn_add_theme)
        left_panel.addStretch()

        # Columna central: lista de temas con búsqueda y contador
        center_panel = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(QLabel("Temas disponibles", self))
        self.theme_count_label = QLabel("", self)
        self.theme_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.theme_count_label)
        center_panel.addLayout(header)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Buscar tema por nombre o descripción...")
        self.search_input.textChanged.connect(self._handle_search_changed)
        center_panel.addWidget(self.search_input)

        self.theme_list = QListWidget(self)
        self.theme_list.currentItemChanged.connect(self._handle_theme_selection)
        center_panel.addWidget(self.theme_list, 1)

        list_buttons = QHBoxLayout()
        btn_rename_theme = QPushButton("Aplicar cambios", self)
        btn_rename_theme.setDefault(False)
        btn_rename_theme.clicked.connect(self._handle_rename_theme)
        btn_delete_theme = QPushButton("Eliminar tema", self)
        btn_delete_theme.setDefault(False)
        btn_delete_theme.clicked.connect(self._handle_delete_theme)
        list_buttons.addWidget(btn_rename_theme)
        list_buttons.addWidget(btn_delete_theme)
        center_panel.addLayout(list_buttons)

        # Columna derecha: palabras y dificultad
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Palabras del tema", self))
        self.difficulty_combo = QComboBox(self)
        self.difficulty_combo.addItems(["fácil", "medio", "difícil"])
        self.difficulty_combo.setCurrentText("medio")
        self.difficulty_combo.currentTextChanged.connect(self._load_words)
        right_panel.addWidget(self.difficulty_combo)
        self.words_table = QTableWidget(self)
        self.words_table.setColumnCount(3)
        self.words_table.setHorizontalHeaderLabels(["ID", "Original", "Normalizada"])
        self.words_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.words_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.words_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        right_panel.addWidget(self.words_table, 1)

        self.new_word_input = QLineEdit(self)
        self.new_word_input.setPlaceholderText("Nueva palabra")
        self.new_word_input.returnPressed.connect(self._handle_add_word)
        btn_add_word = QPushButton("Agregar palabra", self)
        btn_add_word.setDefault(False)
        btn_add_word.clicked.connect(self._handle_add_word)
        btn_suggest_word = QPushButton("Sugerir palabras", self)
        btn_suggest_word.setDefault(False)
        btn_suggest_word.clicked.connect(self._handle_suggest_words)
        btn_delete_word = QPushButton("Eliminar palabra seleccionada", self)
        btn_delete_word.setDefault(False)
        btn_delete_word.clicked.connect(self._handle_delete_word)
        right_panel.addWidget(self.new_word_input)
        right_panel.addWidget(btn_add_word)
        right_panel.addWidget(btn_suggest_word)
        right_panel.addWidget(btn_delete_word)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(center_panel, 1)
        main_layout.addLayout(right_panel, 2)

    def _load_themes(self) -> None:
        current_id = self._theme_id
        self.theme_list.clear()
        try:
            data = themes.list_themes()
            self._themes_cache = data
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Error al cargar temas", str(exc))
            return
        self._render_theme_list(current_id)

    def _render_theme_list(self, restore_id: int | None) -> None:
        """Pinta la lista de temas según el filtro de búsqueda."""
        self.theme_list.blockSignals(True)
        self.theme_list.clear()
        filter_text = self.search_input.text().lower().strip()
        restored_row = -1
        for row_index, theme in enumerate(self._themes_cache):
            name = theme.name
            description = theme.description or ""
            if filter_text and filter_text not in name.lower() and filter_text not in description.lower():
                continue
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, theme.id)
            if description:
                item.setToolTip(description)
            self.theme_list.addItem(item)
            if restore_id is not None and theme.id == restore_id:
                restored_row = self.theme_list.count() - 1

        count = self.theme_list.count()
        self.theme_count_label.setText(f"{count} tema{'s' if count != 1 else ''}")

        if restored_row >= 0:
            self.theme_list.setCurrentRow(restored_row)
        elif self.theme_list.count() > 0:
            self.theme_list.setCurrentRow(0)
        else:
            self._theme_id = None
            self.new_theme_name.clear()
            self.new_theme_desc.clear()
            self.words_table.setRowCount(0)
        self.theme_list.blockSignals(False)

    def _selected_theme_id(self) -> int | None:
        current = self.theme_list.currentItem()
        if current is None:
            return None
        return int(current.data(Qt.ItemDataRole.UserRole))

    def _handle_theme_selection(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        self._theme_id = self._selected_theme_id()
        if current is not None:
            self.new_theme_name.setText(current.text())
            self.new_theme_desc.setText(current.toolTip() or "")
        self._load_words()

    def _handle_search_changed(self) -> None:
        """Filtra la lista de temas mientras se escribe."""
        current_id = self._selected_theme_id()
        self._render_theme_list(current_id)

    def _handle_add_theme(self) -> None:
        name = self.new_theme_name.text()
        description = self.new_theme_desc.text() or None
        logger.info("Creando tema desde botón: '%s'", name)
        if not name.strip():
            QMessageBox.warning(self, "Nombre inválido", "Ingresa un nombre para el tema.")
            return
        try:
            new_id = themes.create_theme(name, description)
            logger.info("Tema creado exitosamente: '%s'", name)
            self._theme_id = new_id
        except ValueError as exc:
            # Tema duplicado
            logger.warning("Intento de crear tema duplicado: '%s'", name)
            QMessageBox.warning(self, "Tema duplicado", str(exc))
            return
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error creando tema '%s': %s", name, str(exc))
            QMessageBox.warning(self, "No se pudo crear el tema", str(exc))
            return
        self.new_theme_name.clear()
        self.new_theme_desc.clear()
        self._load_themes()

    def _handle_submit_theme(self) -> None:
        """
        Envía el formulario con Enter: si no hay tema seleccionado entonces crea uno;
        si hay tema seleccionado aplica cambios. Así evitamos crear duplicados por accidente.
        """
        if self._selected_theme_id() is None:
            self._handle_add_theme()
        else:
            self._handle_rename_theme()

    def _handle_new_theme_form(self) -> None:
        """Prepara el formulario para crear un nuevo tema sin afectar el seleccionado."""
        self._theme_id = None
        self.theme_list.clearSelection()
        self.new_theme_name.clear()
        self.new_theme_desc.clear()
        self.words_table.setRowCount(0)

    def _handle_rename_theme(self) -> None:
        theme_id = self._selected_theme_id()
        name = self.new_theme_name.text()
        description = self.new_theme_desc.text() or None
        logger.info("Aplicando cambios desde Enter: theme_id=%s, name='%s'", theme_id, name)
        if not name.strip():
            QMessageBox.warning(self, "Nombre inválido", "Ingresa un nombre para el tema.")
            return
        try:
            if theme_id is None:
                # Crear nuevo tema
                themes.create_theme(name, description)  # pylint: disable=no-member
                logger.info("Tema creado desde Enter: '%s'", name)
                self.new_theme_name.clear()
                self.new_theme_desc.clear()
            else:
                # Actualizar tema existente
                themes.update_theme(theme_id, name, description)  # pylint: disable=no-member
                logger.info("Tema actualizado: ID %s -> '%s'", theme_id, name)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error en aplicar cambios: %s", str(exc))
            QMessageBox.warning(self, "Error", str(exc))
            return
        self._load_themes()

    def _handle_delete_theme(self) -> None:
        theme_id = self._selected_theme_id()
        if theme_id is None:
            QMessageBox.information(self, "Selecciona un tema", "Elige un tema para eliminar.")
            return
        reply = QMessageBox.question(
            self,
            "Eliminar tema",
            "¿Estás seguro de eliminar el tema seleccionado y todas sus palabras?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            themes.delete_theme(theme_id)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo eliminar el tema", str(exc))
            return
        self._load_themes()
        self.words_table.setRowCount(0)

    def _load_words(self) -> None:
        self.words_table.setRowCount(0)
        if self._theme_id is None:
            return
        difficulty = self.difficulty_combo.currentText()
        try:
            words = themes.get_words_for_theme(self._theme_id, difficulty)  # pylint: disable=no-member
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudieron cargar las palabras", str(exc))
            return
        self.words_table.setRowCount(len(words))
        for row_idx, (word_id, normalized, original) in enumerate(words):
            id_item = QTableWidgetItem(str(word_id))
            id_item.setData(Qt.ItemDataRole.UserRole, word_id)
            original_item = QTableWidgetItem(original)
            normalized_item = QTableWidgetItem(normalized)
            self.words_table.setItem(row_idx, 0, id_item)
            self.words_table.setItem(row_idx, 1, original_item)
            self.words_table.setItem(row_idx, 2, normalized_item)
        self.words_table.resizeColumnsToContents()

    def _handle_add_word(self) -> None:
        theme_id = self._selected_theme_id()
        if theme_id is None:
            QMessageBox.information(
                self,
                "Selecciona un tema",
                "Elige un tema para agregar palabras.",
            )
            return
        word = self.new_word_input.text()
        if not word.strip():
            QMessageBox.warning(self, "Palabra vacía", "Ingresa una palabra.")
            return
        difficulty = self.difficulty_combo.currentText()
        try:
            themes.add_word_to_theme(theme_id, word, difficulty)  # pylint: disable=no-member
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo agregar la palabra", str(exc))
            return
        self.new_word_input.clear()
        self._load_words()

    def _handle_delete_word(self) -> None:
        selected_items = self.words_table.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self,
                "Selecciona una palabra",
                "Elige una palabra para eliminar.",
            )
            return
        word_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if word_id is None:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar palabra",
            "¿Eliminar la palabra seleccionada?",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            themes.delete_word(int(word_id))  # pylint: disable=no-member
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo eliminar la palabra", str(exc))
            return
        self._load_words()

    def _handle_suggest_words(self) -> None:
        theme_id = self._selected_theme_id()
        if theme_id is None:
            QMessageBox.information(
                self,
                "Selecciona un tema",
                "Elige un tema para sugerir palabras.",
            )
            return
        try:
            suggestions = suggest_similar_words(theme_id, limit=10)
            if not suggestions:
                QMessageBox.information(
                    self,
                    "Sin sugerencias",
                    "No se encontraron palabras similares.",
                )
                return
            # Mostrar sugerencias en un diálogo
            suggestion_text = (
                "Palabras sugeridas:\n"
                + "\n".join(f"- {word}" for word in suggestions)
            )
            reply = QMessageBox.question(
                self,
                "Sugerencias de palabras",
                suggestion_text + "\n\n¿Agregar todas las sugerencias?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                difficulty = self.difficulty_combo.currentText()
                for word in suggestions:
                    try:
                        themes.add_word_to_theme(theme_id, word, difficulty)  # pylint: disable=no-member
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.warning("No se pudo agregar sugerencia '%s': %s", word, exc)
                self._load_words()
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Error al sugerir palabras", str(exc))


__all__ = ["TemasDialog"]
