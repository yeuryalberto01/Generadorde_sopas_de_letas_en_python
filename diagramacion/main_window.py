"""Ventana principal del editor de diagramación para sopas de letras."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
)  # pylint: disable=no-name-in-module
from PySide6.QtGui import QAction  # pylint: disable=no-name-in-module

from core import PuzzleGenerationError, generate_puzzle, load_puzzle, save_puzzle
from core.models import PuzzleConfig, PuzzleResult

from .view import DiagramView
from .scene import DiagramScene
from .project_overview_dialog import ProjectOverviewDialog
from .config_dialog import ConfigDialog, show_validation_error
from .exporter import export_scene_to_pdf, export_scene_to_png
from .load_puzzle_dialog import LoadPuzzleDialog


class MainWindow(QMainWindow):
    """Configura la vista principal, menús y acciones auxiliares."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Sopas - Diagramación")
        self.scene = DiagramScene(self)
        self.view = DiagramView(self.scene, self)
        self.setCentralWidget(self.view)

        self.current_config: PuzzleConfig | None = None
        self.current_result: PuzzleResult | None = None
        self._last_config_id: int | None = None

        self.resize(1000, 800)
        self.view.centerOn(self.scene.page_item)
        self._build_menus()
        self.statusBar().showMessage("Listo para generar un nuevo puzzle.")

    def _build_menus(self):
        menu_archivo: QMenu = self.menuBar().addMenu("Archivo")
        export_action = QAction("Exportar...", self)
        export_action.triggered.connect(self._handle_export)
        menu_archivo.addAction(export_action)

        menu_archivo.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        menu_archivo.addAction(exit_action)

        menu_puzzle: QMenu = self.menuBar().addMenu("Puzzle")
        new_action = QAction("Generar nuevo...", self)
        new_action.triggered.connect(self._handle_generate_request)
        menu_puzzle.addAction(new_action)

        regenerate_action = QAction("Regenerar último", self)
        regenerate_action.setEnabled(False)
        regenerate_action.triggered.connect(self._regenerate_last_config)
        menu_puzzle.addAction(regenerate_action)
        self._regenerate_action = regenerate_action

        open_saved_action = QAction("Abrir guardado...", self)
        open_saved_action.triggered.connect(self._handle_open_saved)
        menu_puzzle.addAction(open_saved_action)

        menu_ver: QMenu = self.menuBar().addMenu("Ver")
        center_action = QAction("Centrar página", self)
        center_action.triggered.connect(lambda: self.view.centerOn(self.scene.page_item))
        menu_ver.addAction(center_action)

        menu_ayuda: QMenu = self.menuBar().addMenu("Ayuda")
        overview_action = QAction("Mostrar resumen del proyecto", self)
        overview_action.triggered.connect(self._show_project_overview)
        menu_ayuda.addAction(overview_action)

    def _handle_generate_request(self) -> None:
        dialog = ConfigDialog(self, base_config=self.current_config)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            config = dialog.build_config()
        except Exception as exc:  # pylint: disable=broad-except
            show_validation_error(self, str(exc))
            return
        self._generate_and_display(config, persist=dialog.should_persist())

    def _regenerate_last_config(self) -> None:
        if self.current_config is None:
            QMessageBox.information(
                self,
                "Sin configuraciones",
                "Genera primero un puzzle para poder regenerarlo.",
            )
            return
        self._generate_and_display(self.current_config, persist=True)

    def _handle_open_saved(self) -> None:
        dialog = LoadPuzzleDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        config_id = dialog.selected_config_id()
        if config_id is None:
            return
        try:
            config, result = load_puzzle(config_id)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Error al abrir", str(exc))
            return
        self.current_config = config
        self.current_result = result
        self._last_config_id = config_id
        self.scene.display_puzzle(config, result)
        self._regenerate_action.setEnabled(True)
        self.statusBar().showMessage(f"Puzzle {config_id} cargado desde la base de datos.", 5000)

    def _generate_and_display(self, config: PuzzleConfig, persist: bool) -> None:
        try:
            result = generate_puzzle(config)
        except PuzzleGenerationError as exc:
            QMessageBox.warning(self, "No se pudo generar", str(exc))
            return
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Error inesperado", str(exc))
            return

        config_id = None
        if persist:
            try:
                config_id = save_puzzle(config, result)
            except Exception as exc:  # pylint: disable=broad-except
                QMessageBox.warning(
                    self,
                    "Persistencia fallida",
                    f"El puzzle se generó correctamente, pero no se pudo guardar:\n{exc}",
                )

        self.current_config = config
        self.current_result = result
        self.scene.display_puzzle(config, result)
        self._regenerate_action.setEnabled(True)

        if config_id:
            self._last_config_id = config_id
            self.statusBar().showMessage(f"Puzzle guardado con ID {config_id}.", 5000)
        else:
            self.statusBar().showMessage("Puzzle generado.", 5000)

    def _handle_export(self) -> None:
        if self.current_result is None:
            QMessageBox.information(
                self,
                "Nada que exportar",
                "Genera un puzzle antes de exportarlo.",
            )
            return
        filters = "PDF (*.pdf);;PNG (*.png)"
        default_path = str(Path.home() / "puzzle.pdf")
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar puzzle",
            default_path,
            filters,
        )
        if not path:
            return
        suffix = Path(path).suffix.lower()
        target_path = path
        try:
            if suffix == ".pdf" or "pdf" in selected_filter.lower():
                if suffix != ".pdf":
                    target_path = f"{path}.pdf"
                export_scene_to_pdf(self.scene, target_path)
            else:
                if suffix != ".png":
                    target_path = f"{path}.png"
                export_scene_to_png(self.scene, target_path)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Error al exportar", str(exc))
            return
        self.statusBar().showMessage(f"Puzzle exportado en {target_path}", 5000)

    def _show_project_overview(self):
        dialog = ProjectOverviewDialog(self)
        dialog.exec()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
