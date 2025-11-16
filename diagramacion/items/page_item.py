from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtCore import QRectF, Qt


class PageItem(QGraphicsRectItem):
    def __init__(self, width: float, height: float, page_cfg: dict, theme_cfg: dict | None = None, parent=None):
        super().__init__(parent)
        self.page_cfg = page_cfg
        self.theme_cfg = theme_cfg or {}
        self.setRect(QRectF(0, 0, width, height))

        page_color = self.theme_cfg.get("page_color", "#ffffff")
        self.setBrush(QBrush(QColor(page_color)))
        pen = QPen(QColor(self.theme_cfg.get("grid_line_color", "#cccccc")))
        pen.setWidthF(1.0)
        self.setPen(pen)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, False)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        margins = self.page_cfg["margins_mm"]
        factor = 2.83  # 1 mm ~ 2.83 pt
        left = margins["left"] * factor
        right = margins["right"] * factor
        top = margins["top"] * factor
        bottom = margins["bottom"] * factor

        rect = self.rect()

        guide_pen = QPen(QColor(self.theme_cfg.get("grid_line_color", "#dddddd")))
        guide_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(guide_pen)

        margin_rect = QRectF(
            rect.left() + left,
            rect.top() + top,
            rect.width() - left - right,
            rect.height() - top - bottom,
        )
        painter.drawRect(margin_rect)

    def margin_rect(self) -> QRectF:
        """Devuelve el rectángulo interno delimitado por los márgenes configurados."""
        margins = self.page_cfg["margins_mm"]
        factor = 2.83
        rect = self.rect()
        left = margins["left"] * factor
        right = margins["right"] * factor
        top = margins["top"] * factor
        bottom = margins["bottom"] * factor
        return QRectF(
            rect.left() + left,
            rect.top() + top,
            rect.width() - left - right,
            rect.height() - top - bottom,
        )
