"""Panel con propiedades básicas del elemento seleccionado."""

from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QLabel, QFormLayout, QWidget


class PropertiesPanel(QWidget):
    """Muestra datos básicos de selección (tipo, posición y tamaño)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.type_label = QLabel("-", self)
        self.position_label = QLabel("-", self)
        self.size_label = QLabel("-", self)

        layout = QFormLayout(self)
        layout.addRow("Tipo", self.type_label)
        layout.addRow("Posición (X, Y)", self.position_label)
        layout.addRow("Tamaño (Ancho x Alto)", self.size_label)

    def update_from_items(self, items: Iterable[object]) -> None:
        items = list(items)
        if not items:
            self._set_values("Ninguno", "-", "-")
            return
        if len(items) > 1:
            self._set_values(f"{len(items)} elementos", "-", "-")
            return
        item = items[0]
        rect = QRectF()
        if hasattr(item, "sceneBoundingRect"):
            rect = item.sceneBoundingRect()
        type_name = type(item).__name__
        self._set_values(
            type_name,
            f"{rect.x():.1f}, {rect.y():.1f}",
            f"{rect.width():.1f} x {rect.height():.1f}",
        )

    def _set_values(self, type_value: str, position_value: str, size_value: str) -> None:
        self.type_label.setText(type_value)
        self.position_label.setText(position_value)
        self.size_label.setText(size_value)
