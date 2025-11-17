"""Diálogo para gestionar temas y palabras."""

from __future__ import annotations

from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
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

from core import themes


class TemasDialog(QDialog):
    """Permite crear/editar temas y administrar las palabras asociadas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Temas")
        self.resize(900, 520)
        self._theme_id: int | None = None
        self._build_ui()
        self._load_themes()

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Temas disponibles", self))
        self.theme_list = QListWidget(self)
        self.theme_list.currentItemChanged.connect(self._handle_theme_selection)
        left_panel.addWidget(self.theme_list)

        theme_form = QFormLayout()
        self.new_theme_name = QLineEdit(self)
        self.new_theme_desc = QLineEdit(self)
        theme_form.addRow("Nombre", self.new_theme_name)
        theme_form.addRow("Descripción", self.new_theme_desc)
        left_panel.addLayout(theme_form)

        btn_add_theme = QPushButton("Agregar tema", self)
        btn_add_theme.clicked.connect(self._handle_add_theme)
        btn_rename_theme = QPushButton("Renombrar tema", self)
        btn_rename_theme.clicked.connect(self._handle_rename_theme)
        btn_delete_theme = QPushButton("Eliminar tema", self)
        btn_delete_theme.clicked.connect(self._handle_delete_theme)
        left_panel.addWidget(btn_add_theme)
        left_panel.addWidget(btn_rename_theme)
        left_panel.addWidget(btn_delete_theme)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Palabras del tema", self))
        self.words_table = QTableWidget(self)
        self.words_table.setColumnCount(3)
        self.words_table.setHorizontalHeaderLabels(["ID", "Original", "Normalizada"])
        self.words_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.words_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.words_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        right_panel.addWidget(self.words_table)

        self.new_word_input = QLineEdit(self)
        self.new_word_input.setPlaceholderText("Nueva palabra")
        btn_add_word = QPushButton("Agregar palabra", self)
        btn_add_word.clicked.connect(self._handle_add_word)
        btn_delete_word = QPushButton("Eliminar palabra seleccionada", self)
        btn_delete_word.clicked.connect(self._handle_delete_word)
        right_panel.addWidget(self.new_word_input)
        right_panel.addWidget(btn_add_word)
        right_panel.addWidget(btn_delete_word)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

    def _load_themes(self) -> None:
        current_id = self._theme_id
        self.theme_list.clear()
        try:
            data = themes.list_themes()
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Error al cargar temas", str(exc))
            return
        restored_row = -1
        for row_index, (theme_id, name, description) in enumerate(data):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, theme_id)
            if description:
                item.setToolTip(description)
            self.theme_list.addItem(item)
            if current_id is not None and theme_id == current_id:
                restored_row = row_index
        if restored_row >= 0:
            self.theme_list.setCurrentRow(restored_row)
        elif self.theme_list.count() > 0:
            self.theme_list.setCurrentRow(0)

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

    def _handle_add_theme(self) -> None:
        name = self.new_theme_name.text()
        description = self.new_theme_desc.text() or None
        if not name.strip():
            QMessageBox.warning(self, "Nombre inválido", "Ingresa un nombre para el tema.")
            return
        try:
            themes.create_theme(name, description)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo crear el tema", str(exc))
            return
        self.new_theme_name.clear()
        self.new_theme_desc.clear()
        self._load_themes()

    def _handle_rename_theme(self) -> None:
        theme_id = self._selected_theme_id()
        if theme_id is None:
            QMessageBox.information(self, "Selecciona un tema", "Elige un tema para renombrar.")
            return
        name = self.new_theme_name.text()
        description = self.new_theme_desc.text() or None
        if not name.strip():
            QMessageBox.warning(self, "Nombre inválido", "Ingresa el nuevo nombre para el tema.")
            return
        try:
            themes.update_theme(theme_id, name, description)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo actualizar el tema", str(exc))
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
        try:
            words = themes.get_words_for_theme(self._theme_id)
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
            QMessageBox.information(self, "Selecciona un tema", "Elige un tema para agregar palabras.")
            return
        word = self.new_word_input.text()
        if not word.strip():
            QMessageBox.warning(self, "Palabra vacía", "Ingresa una palabra.")
            return
        try:
            themes.add_word_to_theme(theme_id, word)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo agregar la palabra", str(exc))
            return
        self.new_word_input.clear()
        self._load_words()

    def _handle_delete_word(self) -> None:
        selected_items = self.words_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selecciona una palabra", "Elige una palabra para eliminar.")
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
            themes.delete_word(int(word_id))
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "No se pudo eliminar la palabra", str(exc))
            return
        self._load_words()


__all__ = ["TemasDialog"]
