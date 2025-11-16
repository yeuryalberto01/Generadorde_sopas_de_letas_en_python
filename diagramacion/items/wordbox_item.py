from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QPen, QColor, QFont
from PySide6.QtCore import QRectF, Signal


class WordBoxItem(QGraphicsRectItem):
    position_changed = Signal()

    def __init__(self, page_item, config: dict, parent=None):
        super().__init__(parent)
        self.page_item = page_item
        self.config = config
        self.theme_cfg = config.get("theme", {})

        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        pen = QPen(QColor(self.theme_cfg.get("wordbox_border_color", "#444444")))
        pen.setWidthF(1.5)
        self.setPen(pen)

        self.text = QGraphicsTextItem("Palabras\n(Pieza de ejemplo)", self)
        self.text.setDefaultTextColor(QColor(self.theme_cfg.get("grid_line_color", "#333333")))
        self.text.setFont(QFont("Arial", 10))
        self.text.setPos(10, 10)

    def setRect(self, x: float, y: float, w: float, h: float) -> None:  # type: ignore[override]
        super().setRect(QRectF(x, y, w, h))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange:
            self.position_changed.emit()
        return super().itemChange(change, value)
