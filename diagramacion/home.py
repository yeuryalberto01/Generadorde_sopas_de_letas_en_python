"""Pantalla de inicio con accesos a los módulos principales."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class HomeWidget(QWidget):
    open_temas = Signal()
    open_quick_generator = Signal()
    open_diagramacion = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("¿Qué quieres hacer hoy?", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        btn_temas = QPushButton("📚 Trabajar con Temas", self)
        btn_quick = QPushButton("⚙️ Generador rápido", self)
        btn_diagramacion = QPushButton("🧩 Editor de página (Diagramación)", self)

        for button in (btn_temas, btn_quick, btn_diagramacion):
            button.setMinimumHeight(40)
            button.setStyleSheet("font-size: 16px; text-align: left; padding: 8px;")

        btn_temas.clicked.connect(self.open_temas)
        btn_quick.clicked.connect(self.open_quick_generator)
        btn_diagramacion.clicked.connect(self.open_diagramacion)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(btn_temas)
        layout.addWidget(btn_quick)
        layout.addWidget(btn_diagramacion)
        layout.addStretch()


__all__ = ["HomeWidget"]
