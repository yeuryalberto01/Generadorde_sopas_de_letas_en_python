"""Ventana principal del editor de diagramación para sopas de letras."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (
    QFileDialog,
    QDockWidget,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QStackedWidget,
)  # pylint: disable=no-name-in-module
from PySide6.QtGui import QAction  # pylint: disable=no-name-in-module

from export import export_scene_to_pdf as printer_export_pdf  # nuevo módulo

from core import (
    PuzzleGenerationError,
    generate_puzzle,
    get_words_for_theme,
    list_themes,
    load_config,
    load_puzzle,
    save_puzzle,
)
from core.models import PuzzleConfig, PuzzleResult

from .view import DiagramView
from .scene import DiagramScene
from .project_overview_dialog import ProjectOverviewDialog
from .config_dialog import ConfigDialog, show_validation_error
from .exporter import export_scene_to_png
from .home import HomeWidget
from .load_puzzle_dialog import LoadPuzzleDialog
from .temas_dialog import TemasDialog
from .panels.properties_panel import PropertiesPanel


class MainWindow(QMainWindow):
    """Configura la vista principal, menús y acciones auxiliares."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Sopas - Diagramación")
        self.scene = DiagramScene(self)
        self.view = DiagramView(self.scene, self)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.home = HomeWidget(self)
        self.home.open_temas.connect(self.open_temas_module)
        self.home.open_quick_generator.connect(self.open_quick_generator)
        self.home.open_diagramacion.connect(self.open_diagramacion_module)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.view)
        self.stack.setCurrentWidget(self.home)

        self.properties_panel = PropertiesPanel(self)
        self.properties_dock = QDockWidget("Propiedades", self)
        self.properties_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.properties_dock)
        self.scene.selectionChanged.connect(self._update_properties_panel)

        self.current_config: PuzzleConfig | None = None
        self.current_result: PuzzleResult | None = None
        self._last_config_id: int | None = None

        self.resize(1000, 800)
        self.view.centerOn(self.scene.page_item)
        self._build_menus()
        self._update_properties_panel()
        self.statusBar().showMessage("Listo para generar un nuevo puzzle.")

    def _build_menus(self):
        menu_archivo: QMenu = self.menuBar().addMenu("Archivo")
        export_image_action = QAction("Exportar imagen...", self)
        export_image_action.triggered.connect(self._handle_export_image)
        menu_archivo.addAction(export_image_action)

        export_pdf_action = QAction("Exportar a PDF", self)
        export_pdf_action.triggered.connect(self._handle_export_pdf)
        menu_archivo.addAction(export_pdf_action)

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
        home_action = QAction("Ir al inicio", self)
        home_action.triggered.connect(lambda: self.stack.setCurrentWidget(self.home))
        menu_ver.addAction(home_action)

        menu_temas: QMenu = self.menuBar().addMenu("Temas")
        manage_action = QAction("Gestionar temas...", self)
        manage_action.triggered.connect(self.open_temas_module)
        menu_temas.addAction(manage_action)

        generate_from_theme_action = QAction("Generar desde tema...", self)
        generate_from_theme_action.triggered.connect(self._handle_generate_from_theme)
        menu_temas.addAction(generate_from_theme_action)

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
        self.open_diagramacion_module()
        self.scene.display_puzzle(config, result)
        self._regenerate_action.setEnabled(True)

        if config_id:
            self._last_config_id = config_id
            self.statusBar().showMessage(f"Puzzle guardado con ID {config_id}.", 5000)
        else:
            self.statusBar().showMessage("Puzzle generado.", 5000)

    def open_temas_module(self) -> None:
        dialog = TemasDialog(self)
        dialog.exec()

    def open_diagramacion_module(self) -> None:
        self.stack.setCurrentWidget(self.view)

    def open_quick_generator(self) -> None:
        QMessageBox.information(
            self,
            "Generador rápido",
            "El generador rápido aún no está implementado.",
        )

    def _handle_generate_from_theme(self) -> None:
        available = list_themes()
        if not available:
            QMessageBox.information(
                self,
                "Sin temas",
                "Aún no hay temas creados. Usa 'Gestionar temas...' para agregar uno.",
            )
            return
        names = [name for _, name, _ in available]
        selected_name, ok = QInputDialog.getItem(
            self,
            "Seleccionar tema",
            "Elige un tema para generar la sopa:",
            names,
            editable=False,
        )
        if not ok or not selected_name:
            return
        theme_id = next(tid for tid, name, _ in available if name == selected_name)
        words_data = get_words_for_theme(theme_id)
        if not words_data:
            QMessageBox.information(
                self,
                "Tema sin palabras",
                "El tema seleccionado no tiene palabras registradas.",
            )
            return
        words = [normalized for _, normalized, _ in words_data]
        params = self._default_generation_params()
        try:
            config = PuzzleConfig(
                theme_id=theme_id,
                words=words,
                rows=params["rows"],
                cols=params["cols"],
                difficulty=params["difficulty"],
            )
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Configuración inválida", str(exc))
            return
        self._generate_and_display(config, persist=True)

    def _default_generation_params(self) -> dict:
        if self.current_config:
            return {
                "rows": self.current_config.rows,
                "cols": self.current_config.cols,
                "difficulty": self.current_config.difficulty,
            }
        cfg = load_config()
        rows, cols = cfg.get("grid", {}).get("default_size", (15, 15))
        difficulty = "medium"
        difficulty_options = cfg.get("difficulty")
        if isinstance(difficulty_options, list) and difficulty_options:
            # tomar el valor medio si existe
            mid_index = len(difficulty_options) // 2
            difficulty = str(difficulty_options[mid_index]).lower()
        return {"rows": rows, "cols": cols, "difficulty": difficulty}

    def _handle_export_image(self) -> None:
        if self.current_result is None:
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
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.critical(self, "Error al exportar", str(exc))
            return
        self.statusBar().showMessage(f"Puzzle exportado en {target_path}", 5000)

    def _handle_export_pdf(self) -> None:
        if self.current_result is None:
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
            printer_export_pdf(self.scene, target_path)
        except Exception as exc:  # pylint: disable=broad-except
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
