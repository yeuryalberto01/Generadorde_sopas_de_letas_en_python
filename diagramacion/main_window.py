# pylint: disable=no-name-in-module,missing-module-docstring,missing-class-docstring,missing-function-docstring,broad-exception-caught,line-too-long,trailing-whitespace,ungrouped-imports,unused-import,no-member
"""Ventana principal del editor de diagramación para sopas de letras."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QDockWidget,
)  # pylint: disable=no-name-in-module

from core import load_config
from core.error_book import capture_exception
from core.models import PuzzleConfig, PuzzleResult, Theme

from .config_dialog import ConfigDialog, show_validation_error
from .exporter import export_scene_to_pdf, export_scene_to_png
from .home import HomeWidget
from .load_puzzle_dialog import LoadPuzzleDialog
from .menu_builder import MenuBuilder
from .project_overview_dialog import ProjectOverviewDialog
from .puzzle_controller import PuzzleController
from .scene import DiagramScene
from .temas_dialog import TemasDialog
from .theme_dock import ThemeSelectionDock
from .view import DiagramView
from .panels.properties_panel import PropertiesPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Configura la vista principal, menús y acciones auxiliares."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Sopas - Diagramación")

        # Componentes principales
        self.scene = DiagramScene(self)
        self.view = DiagramView(self.scene, self)
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Configurar barra de menú
        self.menuBar().setNativeMenuBar(True)
        self.menuBar().setVisible(True)

        # Home widget
        self.home = HomeWidget(self)
        self.home.open_temas.connect(self.open_temas_module)
        self.home.open_quick_generator.connect(self.open_quick_generator)
        self.home.open_diagramacion.connect(self.open_diagramacion_module)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.view)
        self.stack.setCurrentWidget(self.home)

        # Panel de propiedades
        self.properties_panel = PropertiesPanel(self)
        self.properties_dock = QDockWidget("Propiedades", self)
        self.properties_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_dock)
        self.scene.selectionChanged.connect(self._update_properties_panel)

        # Controladores
        self.puzzle_controller = PuzzleController(self)
        self.menu_builder = MenuBuilder(self)
        self.theme_dock = ThemeSelectionDock(self, self)

        # Construir UI
        self.menu_builder.build_menus()
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.theme_dock)

        # Configurar ventana
        self.resize(1200, 800)
        self.view.centerOn(self.scene.page_item)
        self._update_properties_panel()
        self.statusBar().showMessage("Listo para generar un nuevo puzzle.")

    # Los menús y docks ahora se construyen en los controladores


    def _handle_generate_request(self) -> None:
        try:
            # Si hay un tema seleccionado, pre-rellenar el ConfigDialog
            selected_theme, selected_difficulty = self.theme_dock.get_selected_theme_and_difficulty()
            initial_config = None
            if selected_theme and selected_difficulty:
                try:
                    initial_config = self.puzzle_controller.create_config_from_theme(
                        selected_theme, selected_difficulty
                    )
                except ValueError as exc:
                    QMessageBox.warning(self, "Error de Configuración", str(exc))
                    return
                except Exception as exc:
                    capture_exception(exc, {"context": "theme_config_creation"})
                    QMessageBox.critical(self, "Error", f"Error al preparar configuración del tema: {exc}")
                    return

            dialog = ConfigDialog(self, base_config=initial_config)
            if dialog.exec() != dialog.DialogCode.Accepted:
                return
            try:
                config = dialog.build_config()
            except Exception as exc:
                capture_exception(exc, {"context": "config_dialog_build"})
                show_validation_error(self, str(exc))
                return
            self.puzzle_controller.generate_from_config(config, persist=dialog.should_persist())
        except Exception as exc:
            capture_exception(exc, {"context": "generate_request"})

    def _regenerate_last_config(self) -> None:
        self.puzzle_controller.regenerate_last()

    def _handle_open_saved(self) -> None:
        try:
            dialog = LoadPuzzleDialog(self)
            if dialog.exec() != dialog.DialogCode.Accepted:
                return
            config_id = dialog.selected_config_id()
            if config_id is None:
                return
            self.puzzle_controller.load_saved_puzzle(config_id)
        except Exception as exc:
            capture_exception(exc, {"context": "open_saved_puzzle"})

    def open_temas_module(self) -> None:
        dialog = TemasDialog(self)
        dialog.exec()
        # Recargar temas en el dock
        self.theme_dock.load_categories()

    def open_diagramacion_module(self) -> None:
        self.stack.setCurrentWidget(self.view)

    def open_quick_generator(self) -> None:
        QMessageBox.information(
            self,
            "Generador rápido",
            "El generador rápido aún no está implementado.",
        )

    def _handle_generate_from_selected_theme(self) -> None:
        selected_theme, selected_difficulty = self.theme_dock.get_selected_theme_and_difficulty()
        if not selected_theme or not selected_difficulty:
            QMessageBox.information(
                self,
                "Selección Incompleta",
                "Por favor, selecciona un Tema y una Dificultad para generar.",
            )
            return
        self.puzzle_controller.generate_from_theme(selected_theme, selected_difficulty)



    def _handle_export_image(self) -> None:
        if not self.puzzle_controller.has_current_puzzle():
            QMessageBox.information(
                self,
                "Nada que exportar",
                "Genera un puzzle antes de exportarlo.",
            )
            return
        filters = "PNG (*.png)"
        default_path = str(Path.home() / "puzzle.png")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar imagen del puzzle",
            default_path,
            filters,
        )
        if not path:
            return
        suffix = Path(path).suffix.lower()
        target_path = path
        try:
            if suffix != ".png":
                target_path = f"{path}.png"
            export_scene_to_png(self.scene, target_path)
        except Exception as exc:
            QMessageBox.critical(self, "Error al exportar", str(exc))
            return
        self.statusBar().showMessage(f"Puzzle exportado en {target_path}", 5000)

    def _handle_export_pdf(self) -> None:
        if not self.puzzle_controller.has_current_puzzle():
            QMessageBox.information(
                self,
                "Nada que exportar",
                "Genera un puzzle antes de exportarlo.",
            )
            return
        default_path = str(Path.home() / "puzzle.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a PDF",
            default_path,
            "PDF (*.pdf)",
        )
        if not path:
            return
        target_path = path if Path(path).suffix.lower() == ".pdf" else f"{path}.pdf"
        try:
            export_scene_to_pdf(self.scene, target_path)
        except Exception as exc:
            QMessageBox.critical(self, "Error al exportar PDF", str(exc))
            return
        self.statusBar().showMessage(f"PDF guardado en {target_path}", 5000)

    def _show_project_overview(self):
        dialog = ProjectOverviewDialog(self)
        dialog.exec()

    def _update_properties_panel(self) -> None:
        if not hasattr(self, "properties_panel"):
            return
        self.properties_panel.update_from_items(self.scene.selectedItems())


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
