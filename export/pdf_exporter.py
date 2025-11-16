"""Exportación de escenas Qt a PDF."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSizeF
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QGraphicsScene


def export_scene_to_pdf(scene: QGraphicsScene, file_path: str) -> None:
    """Renderiza una escena completa en un PDF en la ruta indicada."""
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(target))

    rect = scene.sceneRect()
    printer.setPaperSize(QSizeF(rect.width(), rect.height()), QPrinter.Unit.Point)
    printer.setPageMargins(0, 0, 0, 0, QPrinter.Unit.Point)

    painter = QPainter(printer)
    scene.render(painter, target=rect, source=rect)
    painter.end()
