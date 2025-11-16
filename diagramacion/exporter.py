"""Utilidades para exportar la escena a PNG o PDF."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMarginsF, QRectF, QSize, QSizeF, Qt
from PySide6.QtGui import QImage, QPainter, QPageLayout, QPageSize, QPdfWriter
from PySide6.QtWidgets import QGraphicsScene


def export_scene_to_png(scene: QGraphicsScene, path: str | Path, scale: float = 2.0) -> None:
    """Renderiza la escena en un PNG de alta resolución."""
    rect = scene.sceneRect()
    width = max(1, int(rect.width() * scale))
    height = max(1, int(rect.height() * scale))
    image = QImage(QSize(width, height), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)

    painter = QPainter(image)
    painter.scale(scale, scale)
    scene.render(painter, target=QRectF(0, 0, rect.width(), rect.height()), source=rect)
    painter.end()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError(f"No se pudo guardar el archivo PNG en {path}")


def export_scene_to_pdf(scene: QGraphicsScene, path: str | Path) -> None:
    """Renderiza la escena como PDF usando QPdfWriter."""
    rect = scene.sceneRect()
    pdf_writer = QPdfWriter(str(path))
    page_size = QPageSize(QSizeF(rect.width(), rect.height()), QPageSize.Unit.Point)
    layout = QPageLayout(page_size, QPageLayout.Orientation.Portrait, QMarginsF(0, 0, 0, 0))
    pdf_writer.setPageLayout(layout)

    painter = QPainter(pdf_writer)
    scene.render(painter, target=QRectF(0, 0, rect.width(), rect.height()), source=rect)
    painter.end()


__all__ = ["export_scene_to_png", "export_scene_to_pdf"]
