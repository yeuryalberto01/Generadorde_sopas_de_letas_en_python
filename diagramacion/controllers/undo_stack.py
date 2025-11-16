from PySide6.QtWidgets import QUndoStack


class DiagramUndoStack(QUndoStack):
    """Placeholder de pila de deshacer para futuras acciones de edición."""

    def __init__(self, parent=None):
        super().__init__(parent)
