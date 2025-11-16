from PySide6.QtWidgets import QGraphicsTextItem
from PySide6.QtGui import QFont


class TextItem(QGraphicsTextItem):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsTextItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFont(QFont("Arial", 12))
