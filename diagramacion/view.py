"""Custom view for diagram canvas interactions."""

# Pylint struggles with PySide6 stub discovery; suppress false positives.
# pylint: disable=no-name-in-module
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from PySide6.QtGui import QWheelEvent, QMouseEvent, QPainter, QBrush, QColor


class DiagramView(QGraphicsView):
    """Graphics view that adds zoom and middle-click panning."""

    # The event method names must match Qt's hooks, so keep camelCase.
    # pylint: disable=invalid-name, missing-function-docstring

    def __init__(self, *args, **kwargs):
        """Initialize the view with antialiasing and dark background."""
        super().__init__(*args, **kwargs)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(QBrush(QColor("#131722")))
        self._panning = False
        self._pan_start = None
        self._zoom_factor = 1.0

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom in/out with the mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self._zoom_factor *= zoom_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start panning on middle-button press, otherwise default behavior."""
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Pan the view while the middle button is held."""
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Stop panning on middle-button release."""
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)
