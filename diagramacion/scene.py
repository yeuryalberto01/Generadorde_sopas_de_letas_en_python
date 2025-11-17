from __future__ import annotations

from PySide6.QtWidgets import QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QColor
from core import load_config
from core.models import PuzzleConfig, PuzzleResult
from .items.page_item import PageItem
from .items.puzzle_item import PuzzleItem
from .items.wordbox_item import WordBoxItem
from .controllers.layout_controller import LayoutController


class DiagramScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()

        page_cfg = self.config["page"]
        theme_cfg = self.config.get("theme", {})
        if page_cfg["size"] == "letter":
            width, height = 612, 792
        else:
            width, height = 595, 842

        self.setSceneRect(QRectF(0, 0, width, height))

        self.page_item = PageItem(width, height, page_cfg, theme_cfg)
        self.addItem(self.page_item)

        self.puzzle_item = PuzzleItem(self.page_item, self.config)
        self.wordbox_item = WordBoxItem(self.page_item, self.config)

        self.addItem(self.puzzle_item)
        self.addItem(self.wordbox_item)

        self.layout_controller = LayoutController(self.page_item, self.puzzle_item, self.wordbox_item)
        self._layout_initial()

        self.wordbox_item.position_changed.connect(self.layout_controller.adjust_layout)
        self.placeholder_background, self.placeholder_item = self._build_placeholder()
        self.set_empty_state(True)

    def display_puzzle(self, config: PuzzleConfig, result: PuzzleResult) -> None:
        """Envía los datos de un puzzle a los items visuales."""
        self.puzzle_item.set_grid(result.grid)
        word_order = [position.word for position in result.positions]
        self.wordbox_item.set_words(word_order)
        self.layout_controller.adjust_layout()
        self.set_empty_state(False)

    def _layout_initial(self):
        page_rect = self.page_item.margin_rect()
        mid_y = page_rect.height() / 2

        inset = min(30.0, page_rect.width() * 0.05)
        available_width = max(10.0, page_rect.width() - 2 * inset)

        self.puzzle_item.setPos(0, 0)
        self.puzzle_item.setRect(
            page_rect.left() + inset,
            page_rect.top() + inset,
            available_width,
            mid_y - inset,
        )

        self.wordbox_item.setPos(0, 0)
        self.wordbox_item.setRect(
            page_rect.left() + inset,
            page_rect.top() + mid_y,
            available_width,
            mid_y - inset,
        )

        self.layout_controller.adjust_layout()

    def _build_placeholder(self) -> tuple[QGraphicsRectItem, QGraphicsTextItem]:
        text = (
            "No hay puzzle activo.\n"
            "Configura uno manualmente o usa el generador rápido."
        )
        bg = QGraphicsRectItem()
        bg.setBrush(QColor(255, 255, 255, 235))
        bg.setPen(QColor(0, 0, 0, 40))
        bg.setZValue(9)
        self.addItem(bg)
        item = self.addText(text, QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        item.setDefaultTextColor(QColor("#384253"))
        item.setZValue(10)
        self._position_placeholder(bg, item)
        return bg, item

    def _position_placeholder(self, bg: QGraphicsRectItem, text_item: QGraphicsTextItem) -> None:
        margin_rect = self.page_item.margin_rect()
        padding = 40
        size = text_item.boundingRect().adjusted(-padding, -padding, padding, padding)
        x = margin_rect.center().x() - size.width() / 2
        y = margin_rect.center().y() - size.height() / 2
        bg.setRect(x, y, size.width(), size.height())
        text_item.setPos(x + padding, y + padding / 2)

    def set_empty_state(self, visible: bool, message: str | None = None) -> None:
        if self.placeholder_item is None or self.placeholder_background is None:
            return
        if message:
            self.placeholder_item.setPlainText(message)
            self._position_placeholder(self.placeholder_background, self.placeholder_item)
        self.placeholder_item.setVisible(visible)
        self.placeholder_background.setVisible(visible)
