from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import QRectF


class PuzzleItem(QGraphicsRectItem):
    def __init__(self, page_item, config: dict, parent=None):
        super().__init__(parent)
        self.page_item = page_item
        self.config = config
        self.theme_cfg = config.get("theme", {})
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        pen = QPen(QColor(self.theme_cfg.get("grid_line_color", "#999999")))
        pen.setWidthF(1.0)
        self.setPen(pen)

    def setRect(self, x: float, y: float, w: float, h: float) -> None:  # type: ignore[override]
        super().setRect(QRectF(x, y, w, h))

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        rect = self.rect()
        rows, cols = self.config.get("grid", {}).get("default_size", (15, 15))
        if rows <= 0 or cols <= 0:
            return
        cell_w = rect.width() / cols
        cell_h = rect.height() / rows

        grid_pen = QPen(QColor(self.theme_cfg.get("grid_line_color", "#999999")))
        painter.setPen(grid_pen)

        for col in range(1, cols):
            x = rect.left() + col * cell_w
            painter.drawLine(x, rect.top(), x, rect.bottom())
        for row in range(1, rows):
            y = rect.top() + row * cell_h
            painter.drawLine(rect.left(), y, rect.right(), y)
