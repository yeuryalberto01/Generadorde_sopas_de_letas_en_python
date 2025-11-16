# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring
from PySide6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QGraphicsItem  # pylint: disable=no-name-in-module
from PySide6.QtGui import QPen, QColor, QFont  # pylint: disable=no-name-in-module
from PySide6.QtCore import QRectF, Signal  # pylint: disable=no-name-in-module


class WordBoxItem(QGraphicsObject):
    position_changed = Signal()

    def __init__(self, page_item, config: dict, parent=None):
        super().__init__(parent)
        self.page_item = page_item
        self.config = config
        self.theme_cfg = config.get("theme", {})

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        pen = QPen(QColor(self.theme_cfg.get("wordbox_border_color", "#444444")))
        pen.setWidthF(1.5)
        self._pen = pen

        self._rect = QRectF()

        self.text = QGraphicsTextItem("Palabras\n(Pieza de ejemplo)", self)
        self.text.setDefaultTextColor(QColor(self.theme_cfg.get("grid_line_color", "#333333")))
        self.text.setFont(QFont("Arial", 10))
        self.text.setPos(10, 10)
        self._words: list[str] = []

    def setRect(self, x: float, y: float, w: float, h: float) -> None:  # pylint: disable=invalid-name
        self._rect = QRectF(x, y, w, h)
        self.text.setTextWidth(max(0.0, w - 20.0))
        self.update()

    def boundingRect(self):  # pylint: disable=invalid-name
        return self._rect

    def paint(self, painter, option, widget=None):  # pylint: disable=unused-argument
        painter.setPen(self._pen)
        painter.drawRect(self._rect)

    def set_words(self, words: list[str]) -> None:
        self._words = words
        if words:
            columns = []
            chunk = max(1, len(words) // 3)
            if len(words) <= 12:
                chunk = len(words)
            for idx in range(0, len(words), chunk):
                columns.append("\n".join(words[idx : idx + chunk]))
            joined = "\n\n".join(columns)
        else:
            joined = "Sin palabras configuradas."
        self.text.setPlainText(joined)
        self.text.setTextWidth(max(0.0, self._rect.width() - 20.0))
        self.update()

    def itemChange(self, change, value):  # pylint: disable=invalid-name
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.position_changed.emit()
        return super().itemChange(change, value)
