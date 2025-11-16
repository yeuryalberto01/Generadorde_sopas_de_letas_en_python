from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import QRectF
from core import load_config
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
