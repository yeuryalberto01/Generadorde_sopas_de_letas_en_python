"""Diálogo para seleccionar puzzles guardados previamente."""

from __future__ import annotations

from typing import List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core import list_recent_puzzles


class LoadPuzzleDialog(QDialog):
    """Presenta un listado simple de puzzles almacenados en SQLite."""

    headers = ["ID", "Dificultad", "Dimensiones", "Creado"]

    def __init__(self, parent=None, limit: int = 25):
        super().__init__(parent)
        self.setWindowTitle("Abrir puzzle guardado")
        self.resize(540, 360)
        self._limit = limit
        self._selected_id: int | None = None
        self._rows: List[Tuple[int, str, int, int, str]] = []
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.info_label = QLabel(
            "Selecciona un puzzle y presiona Abrir. Los más recientes aparecen primero.",
            self,
        )
        layout.addWidget(self.info_label)

        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._sync_selection)
        self.table.doubleClicked.connect(self._accept_if_valid)
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._buttons = buttons

    def _populate(self) -> None:
        try:
            self._rows = list_recent_puzzles(limit=self._limit)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(
                self,
                "No se pudo leer la base de datos",
                str(exc),
            )
            self._rows = []
        self.table.setRowCount(len(self._rows))
        for row_idx, (config_id, difficulty, rows, cols, created_at) in enumerate(self._rows):
            values = [
                str(config_id),
                difficulty,
                f"{rows} x {cols}",
                created_at,
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, config_id)
                self.table.setItem(row_idx, col_idx, item)
        self.table.resizeColumnsToContents()
        self._buttons.button(QDialogButtonBox.StandardButton.Open).setEnabled(bool(self._rows))
        if self._rows:
            self.table.selectRow(0)

    def _sync_selection(self) -> None:
        items = self.table.selectedItems()
        if not items:
            self._selected_id = None
            self._buttons.button(QDialogButtonBox.StandardButton.Open).setEnabled(False)
            return
        row = items[0].row()
        cell = self.table.item(row, 0)
        self._selected_id = int(cell.data(Qt.ItemDataRole.UserRole))
        self._buttons.button(QDialogButtonBox.StandardButton.Open).setEnabled(True)

    def _accept_if_valid(self) -> None:
        if self._selected_id is not None:
            self.accept()

    def selected_config_id(self) -> int | None:
        return self._selected_id


__all__ = ["LoadPuzzleDialog"]
