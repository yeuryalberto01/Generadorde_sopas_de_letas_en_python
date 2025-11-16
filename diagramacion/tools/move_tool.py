class MoveTool:
    """Placeholder para herramienta de movimiento manual."""

    def __init__(self):
        self.scene = None

    def activate(self, scene):
        self.scene = scene

    def deactivate(self):
        self.scene = None
