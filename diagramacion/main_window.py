from PySide6.QtWidgets import QMainWindow, QMenu, QAction
from .view import DiagramView
from .scene import DiagramScene


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Sopas - Diagramación")
        self.scene = DiagramScene(self)
        self.view = DiagramView(self.scene, self)
        self.setCentralWidget(self.view)

        self.resize(1000, 800)
        self.view.centerOn(self.scene.page_item)
        self._build_menus()

    def _build_menus(self):
        menu_archivo: QMenu = self.menuBar().addMenu("Archivo")
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        menu_archivo.addAction(exit_action)

        menu_ver: QMenu = self.menuBar().addMenu("Ver")
        center_action = QAction("Centrar página", self)
        center_action.triggered.connect(lambda: self.view.centerOn(self.scene.page_item))
        menu_ver.addAction(center_action)
