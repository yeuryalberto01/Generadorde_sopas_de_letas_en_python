"""Constructor de menús para la ventana principal."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QMenu  # pylint: disable=no-name-in-module
from PySide6.QtGui import QAction  # pylint: disable=no-name-in-module


class MenuBuilder:
    """Construye y configura los menús de la aplicación."""

    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.icons = {
            "export_image": None,
            "export_pdf": None,
            "exit": None,
            "generate": None,
            "regenerate": None,
            "open": None,
            "center": None,
            "home": None,
            "themes": None,
            "help": None,
            "play": None,
        }

    def build_menus(self) -> None:
        """Construye todos los menús."""
        self._build_file_menu()
        self._build_puzzle_menu()
        self._build_view_menu()
        self._build_themes_menu()
        self._build_help_menu()

    def _build_file_menu(self) -> None:
        menu = self.main_window.menuBar().addMenu("Archivo")
        print(f"Menú Archivo creado: {menu}")  # Debug
        self._add_action(menu, "Exportar imagen...", self.main_window._handle_export_image, "export_image")  # pylint: disable=protected-access
        self._add_action(menu, "Exportar a PDF", self.main_window._handle_export_pdf, "export_pdf")  # pylint: disable=protected-access
        menu.addSeparator()
        self._add_action(menu, "Salir", self.main_window.close, "exit")

    def _build_puzzle_menu(self) -> None:
        menu = self.main_window.menuBar().addMenu("Puzzle")
        self._add_action(menu, "Generar nuevo (manual)...",
                         self.main_window._handle_generate_request, "generate")  # pylint: disable=protected-access
        regenerate_action = self._add_action(menu, "Regenerar último",
                                             self.main_window._regenerate_last_config, "regenerate")  # pylint: disable=protected-access
        regenerate_action.setEnabled(False)
        self.main_window._regenerate_action = regenerate_action  # pylint: disable=protected-access
        self._add_action(menu, "Abrir guardado...",
                         self.main_window._handle_open_saved, "open")  # pylint: disable=protected-access

    def _build_view_menu(self) -> None:
        menu = self.main_window.menuBar().addMenu("Ver")
        self._add_action(menu, "Centrar página",
                         lambda: self.main_window.view.centerOn(self.main_window.scene.page_item), "center")
        self._add_action(menu, "Ir al inicio",
                         lambda: self.main_window.stack.setCurrentWidget(self.main_window.home), "home")

    def _build_themes_menu(self) -> None:
        menu = self.main_window.menuBar().addMenu("Temas")
        self._add_action(menu, "Gestionar temas...", self.main_window.open_temas_module, "themes")

    def _build_help_menu(self) -> None:
        menu = self.main_window.menuBar().addMenu("Ayuda")
        self._add_action(menu, "Mostrar resumen del proyecto",
                         self.main_window._show_project_overview, "help")  # pylint: disable=protected-access

    def _add_action(self, menu: QMenu, text: str, handler, icon_key: str) -> QAction:
        # CORREGIDO: Crear la acción correctamente
        action = QAction(text, self.main_window)
        if self.icons[icon_key] is not None:
            action.setIcon(self.icons[icon_key])
        action.triggered.connect(handler)
        menu.addAction(action)
        print(f"Acción añadida: '{text}' al menú '{menu.title()}'")
        return action

