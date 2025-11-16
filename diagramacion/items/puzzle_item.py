# pylint: disable=no-name-in-module,missing-module-docstring,missing-class-docstring,missing-function-docstring
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtGui import QPen, QColor, QFont
from PySide6.QtCore import QRectF, Qt


class PuzzleItem(QGraphicsRectItem):
    def __init__(self, page_item, config: dict, parent=None):
        super().__init__(parent)
        self.page_item = page_item
        self.config = config
        self.theme_cfg = config.get("theme", {})
        self.grid_data: list[list[str]] = []
        default_rows, default_cols = config.get("grid", {}).get("default_size", (15, 15))
        self.grid_rows = default_rows
        self.grid_cols = default_cols
        self.text_font = QFont("Courier New", 12)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        pen = QPen(QColor(self.theme_cfg.get("grid_line_color", "#999999")))
        pen.setWidthF(1.0)
        self.setPen(pen)

    def setRect(self, x: float, y: float, w: float, h: float) -> None:  # type: ignore[override]  # pylint: disable=invalid-name
        super().setRect(QRectF(x, y, w, h))

    def set_grid(self, grid: list[list[str]]) -> None:
        self.grid_data = grid
        if grid and grid[0]:
            self.grid_rows = len(grid)
            self.grid_cols = len(grid[0])
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        rect = self.rect()
        rows = max(1, self.grid_rows)
        cols = max(1, self.grid_cols)
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

        if not self.grid_data:
            return

        painter.setFont(self.text_font)
        painter.setPen(QColor(self.theme_cfg.get("text_color", "#111111")))
        for row_idx, row_data in enumerate(self.grid_data):
            for col_idx, letter in enumerate(row_data):
                if not letter:
                    continue
                cell_rect = QRectF(
                    rect.left() + col_idx * cell_w,
                    rect.top() + row_idx * cell_h,
                    cell_w,
                    cell_h,
                )
                painter.drawText(cell_rect, Qt.AlignmentFlag.AlignCenter, letter)
