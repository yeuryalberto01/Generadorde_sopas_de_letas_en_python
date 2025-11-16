from PySide6.QtCore import QRectF


class LayoutController:
    def __init__(self, page_item, puzzle_item, wordbox_item):
        self.page_item = page_item
        self.puzzle_item = puzzle_item
        self.wordbox_item = wordbox_item

    def adjust_layout(self):
        margin_rect: QRectF = self.page_item.margin_rect()
        wordbox_rect = self.wordbox_item.sceneBoundingRect()
        center_y = wordbox_rect.center().y()
        page_center_y = margin_rect.center().y()

        inset = min(30.0, margin_rect.width() * 0.05)
        gutter = min(20.0, margin_rect.height() * 0.05)

        # Mantener el alto actual de la wordbox pero sin invadir márgenes
        word_height = min(wordbox_rect.height(), margin_rect.height() * 0.45)
        available_width = max(10.0, margin_rect.width() - 2 * inset)

        if center_y <= page_center_y:
            # Wordbox arriba
            word_top = margin_rect.top() + inset
            puzzle_top = word_top + word_height + gutter
            puzzle_height = max(10.0, margin_rect.bottom() - puzzle_top - inset)
        else:
            # Wordbox abajo
            word_top = margin_rect.bottom() - inset - word_height
            puzzle_top = margin_rect.top() + inset
            puzzle_height = max(10.0, word_top - gutter - puzzle_top)

        # Actualizar wordbox
        self.wordbox_item.setPos(0, 0)
        self.wordbox_item.setRect(
            margin_rect.left() + inset,
            word_top,
            available_width,
            word_height,
        )

        # Actualizar puzzle
        self.puzzle_item.setPos(0, 0)
        self.puzzle_item.setRect(
            margin_rect.left() + inset,
            puzzle_top,
            available_width,
            puzzle_height,
        )
