from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtGui import QPixmap


class ImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap | None = None, parent=None):
        super().__init__(pixmap or QPixmap(), parent)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, True)
