# pylint: disable=no-name-in-module,missing-module-docstring,missing-class-docstring,missing-function-docstring,broad-exception-caught,line-too-long,trailing-whitespace,ungrouped-imports,unused-import,no-member
"""Ventana principal del editor de diagramación para sopas de letras."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt, QSize  # pylint: disable=no-name-in-module
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)  # pylint: disable=no-name-in-module
from PySide6.QtGui import QAction  # pylint: disable=no-name-in-module

from export import export_scene_to_pdf as printer_export_pdf  # nuevo módulo

from core import (
    PuzzleGenerationError,
    generate_puzzle,
    load_config,
    load_puzzle,
    save_puzzle,
)
from core import themes
from core.models import Category, PuzzleConfig, PuzzleResult, Theme, ThemeWordList

from .view import DiagramView
from .scene import DiagramScene
from .project_overview_dialog import ProjectOverviewDialog
from .config_dialog import ConfigDialog, show_validation_error
from .exporter import export_scene_to_png
from .home import HomeWidget
from .load_puzzle_dialog import LoadPuzzleDialog
from .temas_dialog import TemasDialog
from .panels.properties_panel import PropertiesPanel
from .quick_generator_dialog import QuickGeneratorDialog


class MainWindow(QMainWindow):
    """Configura la vista principal, menús y acciones auxiliares."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Sopas - Diagramación")

        self.icons: dict[str, object | None] = {}
        self._load_icons()

        self.scene = DiagramScene(self)
        self.view = DiagramView(self.scene, self)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self._hint_message: str = ""
        self.home = HomeWidget(self)
        self.home.open_temas.connect(self.open_temas_module)
        self.home.open_quick_generator.connect(self.open_quick_generator)
        self.home.open_diagramacion.connect(self.open_diagramacion_module)
        self.editor_page = self._build_editor_page()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.editor_page)
        self.stack.setCurrentWidget(self.home)

        self.theme_selection_dock: QDockWidget | None = None
        self.properties_panel: PropertiesPanel | None = None
        self.properties_dock: QDockWidget | None = None
        self.window_menu: QMenu | None = None
        self._dock_actions: dict[str, QAction] = {}

        self.current_config: PuzzleConfig | None = None
        self.current_result: PuzzleResult | None = None
        self._last_config_id: int | None = None
        self._selected_theme: Optional[Theme] = None
        self._selected_difficulty: Optional[str] = None

        self.resize(1200, 800) # Aumentar tamaño para el nuevo dock
        self.view.centerOn(self.scene.page_item)
        self._create_actions()
        self._build_menus()
        self._build_toolbar()
        self.statusBar().showMessage("Listo para generar un nuevo puzzle.")
        self._update_hint_banner(
            "Selecciona un tema o usa el generador rápido para crear tu primera sopa."
        )
        self.scene.set_empty_state(
            True,
            "No hay puzzle activo.\nElige una acción para comenzar.",
        )

        # Cargar categorías y temas al inicio
        self._load_categories_into_combo()
        self._set_editor_mode(False)
        self._update_editor_state()

    def _load_icons(self) -> None:
        def _icon(name: str):
            try:
                return qta.icon(name)
            except Exception:
                return None

        self.icons = {
            "export_image": _icon("fa5s.image"),
            "export_pdf": _icon("fa5s.file-pdf"),
            "exit": _icon("fa5s.power-off"),
            "generate": _icon("fa5s.magic"),
            "quick": _icon("fa5s.bolt"),
            "regenerate": _icon("fa5s.redo"),
            "open": _icon("fa5s.folder-open"),
            "center": _icon("fa5s.crosshairs"),
            "home": _icon("fa5s.home"),
            "themes": _icon("fa5s.book"),
            "help": _icon("fa5s.question-circle"),
            "play": _icon("fa5s.play"),
        }

    def _apply_icon(self, widget, key: str) -> None:
        icon = self.icons.get(key)
        if icon:
            widget.setIcon(icon)

    def _build_editor_page(self) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.hint_banner = self._create_hint_banner(container)
        layout.addWidget(self.hint_banner)
        layout.addWidget(self.view)
        return container

    def _set_editor_mode(self, enabled: bool) -> None:
        if hasattr(self, "main_toolbar") and self.main_toolbar is not None:
            self.main_toolbar.setVisible(enabled)
        self._apply_dock_visibility()
        self._update_hint_visibility()

    def _update_editor_state(self) -> None:
        has_puzzle = self.current_result is not None
        can_regenerate = self.current_config is not None
        for action in (
            self.action_export_image,
            self.action_export_pdf,
            self.action_center_page,
        ):
            action.setEnabled(has_puzzle)
        self.action_regenerate.setEnabled(can_regenerate)
        self._update_hint_visibility()
        self.scene.set_empty_state(not has_puzzle)

    def _update_hint_visibility(self) -> None:
        if hasattr(self, "hint_banner"):
            should_show = (
                self.stack.currentWidget() is self.editor_page
                and self.current_result is None
                and bool(self._hint_message)
            )
            self.hint_banner.setVisible(should_show)

    def _create_hint_banner(self, parent: QWidget) -> QWidget:
        frame = QFrame(parent)
        frame.setObjectName("hintBanner")
        frame.setStyleSheet(
            """
            QFrame#hintBanner {
                background-color: #1c2235;
                border-bottom: 1px solid #0f131f;
            }
            QFrame#hintBanner QPushButton {
                background-color: #2f3a59;
                color: #f4f6fb;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QFrame#hintBanner QPushButton:hover {
                background-color: #3d4b74;
            }
            """
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        self.hint_label = QLabel("", frame)
        self.hint_label.setStyleSheet("font-weight: 600; color: #e2e8ff;")
        layout.addWidget(self.hint_label, 1)

        buttons_container = QWidget(frame)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)

        btn_generate = QPushButton("Generar manual", buttons_container)
        btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_icon(btn_generate, "generate")
        btn_generate.clicked.connect(self._handle_generate_request)
        buttons_layout.addWidget(btn_generate)

        btn_quick = QPushButton("Generador rápido", buttons_container)
        btn_quick.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_icon(btn_quick, "quick")
        btn_quick.clicked.connect(self.open_quick_generator)
        buttons_layout.addWidget(btn_quick)

        btn_theme = QPushButton("Ver temas", buttons_container)
        btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_icon(btn_theme, "themes")
        btn_theme.clicked.connect(self.open_temas_module)
        buttons_layout.addWidget(btn_theme)

        layout.addWidget(buttons_container, 0, Qt.AlignmentFlag.AlignRight)
        return frame

    def _update_hint_banner(self, message: str | None) -> None:
        if not hasattr(self, "hint_label"):
            return
        if message is None:
            self._hint_message = ""
        else:
            self._hint_message = message
        self.hint_label.setText(self._hint_message)
        self._update_hint_visibility()

    def _create_actions(self) -> None:
        self.action_export_image = QAction(self.icons.get("export_image"), "Exportar imagen...", self)
        self.action_export_image.triggered.connect(self._handle_export_image)

        self.action_export_pdf = QAction(self.icons.get("export_pdf"), "Exportar a PDF", self)
        self.action_export_pdf.triggered.connect(self._handle_export_pdf)

        self.action_exit = QAction(self.icons.get("exit"), "Salir", self)
        self.action_exit.triggered.connect(self.close)

        self.action_generate = QAction(self.icons.get("generate"), "Generar nuevo (manual)...", self)
        self.action_generate.triggered.connect(self._handle_generate_request)

        self.action_quick_generator = QAction(self.icons.get("quick"), "Generador rápido...", self)
        self.action_quick_generator.triggered.connect(self.open_quick_generator)

        self.action_regenerate = QAction(self.icons.get("regenerate"), "Regenerar último", self)
        self.action_regenerate.setEnabled(False)
        self.action_regenerate.triggered.connect(self._regenerate_last_config)

        self.action_open_saved = QAction(self.icons.get("open"), "Abrir guardado...", self)
        self.action_open_saved.triggered.connect(self._handle_open_saved)

        self.action_center_page = QAction(self.icons.get("center"), "Centrar página", self)
        self.action_center_page.triggered.connect(lambda: self.view.centerOn(self.scene.page_item))

        self.action_go_home = QAction(self.icons.get("home"), "Ir al inicio", self)
        self.action_go_home.triggered.connect(self._go_home)

        self.action_manage_themes = QAction(self.icons.get("themes"), "Gestionar temas...", self)
        self.action_manage_themes.triggered.connect(self.open_temas_module)

        self.action_show_overview = QAction(self.icons.get("help"), "Mostrar resumen del proyecto", self)
        self.action_show_overview.triggered.connect(self._show_project_overview)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Accesos rápidos", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.addAction(self.action_generate)
        toolbar.addAction(self.action_quick_generator)
        toolbar.addAction(self.action_regenerate)
        toolbar.addSeparator()
        toolbar.addAction(self.action_open_saved)
        toolbar.addAction(self.action_manage_themes)
        toolbar.addSeparator()
        toolbar.addAction(self.action_export_image)
        toolbar.addAction(self.action_export_pdf)
        toolbar.addSeparator()
        toolbar.addAction(self.action_center_page)
        toolbar.addAction(self.action_go_home)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.main_toolbar = toolbar
        self.main_toolbar.setVisible(True)
        toolbar.setStyleSheet(
            "QToolBar { border: 0; background-color: #181c2a; spacing: 6px; }"
        )

    def _go_home(self) -> None:
        self.stack.setCurrentWidget(self.home)
        self._update_hint_banner("Elige un módulo para continuar.")
        self.home.restart_intro()
        self._set_editor_mode(False)
        self._hide_editor_docks()
        self._update_editor_state()
    def _build_menus(self):
        menu_archivo: QMenu = self.menuBar().addMenu("Archivo")
        menu_archivo.addAction(self.action_export_image)
        menu_archivo.addAction(self.action_export_pdf)
        menu_archivo.addSeparator()
        menu_archivo.addAction(self.action_exit)

        menu_puzzle: QMenu = self.menuBar().addMenu("Puzzle")
        menu_puzzle.addAction(self.action_generate)
        menu_puzzle.addAction(self.action_quick_generator)
        menu_puzzle.addAction(self.action_regenerate)
        menu_puzzle.addSeparator()
        menu_puzzle.addAction(self.action_open_saved)

        menu_ver: QMenu = self.menuBar().addMenu("Ver")
        menu_ver.addAction(self.action_center_page)
        menu_ver.addAction(self.action_go_home)

        self.window_menu = self.menuBar().addMenu("Ventana")

        menu_temas: QMenu = self.menuBar().addMenu("Temas")
        menu_temas.addAction(self.action_manage_themes)

        menu_ayuda: QMenu = self.menuBar().addMenu("Ayuda")
        menu_ayuda.addAction(self.action_show_overview)

    def _ensure_theme_dock(self) -> None:
        if hasattr(self, "theme_selection_dock") and self.theme_selection_dock is not None:
            return

        self.theme_selection_dock = QDockWidget("Selección de Tema", self)
        theme_selection_widget = QWidget()
        layout = QVBoxLayout(theme_selection_widget)

        helper_label = QLabel(
            "Filtra por categoría, elige un tema y define la dificultad para generar en un clic.",
            theme_selection_widget,
        )
        helper_label.setWordWrap(True)
        helper_label.setStyleSheet("color: #4b5563;")
        layout.addWidget(helper_label)

        # Categoría
        category_group = QGroupBox("Categoría")
        category_layout = QVBoxLayout(category_group)
        self.category_combo = QComboBox(self)
        self.category_combo.addItem("Todas las Categorías", None)
        self.category_combo.currentIndexChanged.connect(self._handle_category_selection_main_window)
        category_layout.addWidget(self.category_combo)
        layout.addWidget(category_group)

        # Tema
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout(theme_group)
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("Seleccionar Tema", None)
        self.theme_combo.currentIndexChanged.connect(self._handle_theme_selection_main_window)
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)

        # Dificultad
        difficulty_group = QGroupBox("Dificultad")
        difficulty_layout = QVBoxLayout(difficulty_group)
        self.difficulty_combo = QComboBox(self)
        self.difficulty_combo.addItem("Seleccionar Dificultad", None)
        difficulty_layout.addWidget(self.difficulty_combo)
        layout.addWidget(difficulty_group)

        # Botones de acción
        action_buttons_layout = QVBoxLayout()
        btn_generate_from_theme = QPushButton("Generar desde Tema", self)
        self._apply_icon(btn_generate_from_theme, "play")
        btn_generate_from_theme.clicked.connect(self._handle_generate_from_selected_theme)
        action_buttons_layout.addWidget(btn_generate_from_theme)

        btn_manage_themes = QPushButton("Gestionar Temas", self)
        self._apply_icon(btn_manage_themes, "themes")
        btn_manage_themes.clicked.connect(self.open_temas_module)
        action_buttons_layout.addWidget(btn_manage_themes)
        layout.addLayout(action_buttons_layout)

        layout.addStretch() # Empujar los elementos hacia arriba

        self.theme_selection_dock.setWidget(theme_selection_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.theme_selection_dock)
        self.theme_selection_dock.hide()
        self._register_dock_action(
            "theme_panel",
            "Panel de temas",
            self._ensure_theme_dock,
            "theme_selection_dock",
            default=True,
        )

    def _build_theme_selection_dock(self) -> None:
        self._ensure_theme_dock()

    def _register_dock_action(
        self,
        key: str,
        label: str,
        ensure_callback,
        dock_attr: str,
        *,
        default: bool = True,
    ) -> None:
        if self.window_menu is None or key in self._dock_actions:
            return
        action = QAction(label, self)
        action.setCheckable(True)
        action.setChecked(default)
        action.toggled.connect(
            lambda checked, attr=dock_attr, ensure=ensure_callback: self._toggle_dock(attr, ensure, checked)
        )
        self.window_menu.addAction(action)
        self._dock_actions[key] = action

    def _toggle_dock(self, dock_attr: str, ensure_callback, visible: bool) -> None:
        ensure_callback()
        self._apply_dock_visibility()

    def _ensure_properties_dock(self) -> None:
        if self.properties_dock is not None:
            return
        self.properties_panel = PropertiesPanel(self)
        dock = QDockWidget("Propiedades", self)
        dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.properties_dock = dock
        self.properties_dock.hide()
        self.scene.selectionChanged.connect(self._update_properties_panel)
        self._register_dock_action(
            "properties_panel",
            "Propiedades",
            self._ensure_properties_dock,
            "properties_dock",
            default=True,
        )

    def _ensure_editor_docks(self) -> None:
        self._ensure_theme_dock()
        self._ensure_properties_dock()
        self._apply_dock_visibility()

    def _hide_editor_docks(self) -> None:
        if hasattr(self, "theme_selection_dock") and self.theme_selection_dock is not None:
            self.theme_selection_dock.hide()
        if self.properties_dock is not None:
            self.properties_dock.hide()
    def _apply_dock_visibility(self) -> None:
        in_editor = self.stack.currentWidget() is self.editor_page
        theme_action = self._dock_actions.get("theme_panel")
        if self.theme_selection_dock:
            should_show = in_editor and (theme_action is None or theme_action.isChecked())
            self.theme_selection_dock.setVisible(should_show)
        prop_action = self._dock_actions.get("properties_panel")
        if self.properties_dock:
            should_show = in_editor and (prop_action is None or prop_action.isChecked())
            self.properties_dock.setVisible(should_show)

    def _load_categories_into_combo(self) -> None:
        self._ensure_theme_dock()
        if not hasattr(self, "category_combo"):
            return
        self.category_combo.clear()
        self.category_combo.addItem("Todas las Categorías", None)
        try:
            categories = themes.list_categories()
            for cat in categories:
                self.category_combo.addItem(cat.name, cat.id)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error al cargar categorías: {exc}")
        self.theme_selection_dock.hide()
        self._load_themes_into_combo() # Cargar temas para la categoría inicial

    def _handle_category_selection_main_window(self) -> None:
        self._load_themes_into_combo()

    def _load_themes_into_combo(self) -> None:
        self.theme_combo.clear()
        self.theme_combo.addItem("Seleccionar Tema", None)
        self._selected_theme = None # Resetear tema seleccionado

        selected_category_id = self.category_combo.currentData()
        try:
            all_themes = themes.list_themes()
            filtered_themes = [
                t for t in all_themes
                if selected_category_id is None or (t.category and t.category.id == selected_category_id)
            ]
            for t in filtered_themes:
                self.theme_combo.addItem(t.name, t.id)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error al cargar temas: {exc}")
        self._load_difficulties_into_combo() # Cargar dificultades para el tema inicial

    def _handle_theme_selection_main_window(self) -> None:
        theme_id = self.theme_combo.currentData()
        if theme_id is not None:
            try:
                self._selected_theme = themes.get_theme(theme_id)
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Error al cargar el tema: {exc}")
                self._selected_theme = None
        else:
            self._selected_theme = None
        self._load_difficulties_into_combo()

    def _load_difficulties_into_combo(self) -> None:
        self.difficulty_combo.clear()
        self.difficulty_combo.addItem("Seleccionar Dificultad", None)
        self._selected_difficulty = None # Resetear dificultad seleccionada

        if self._selected_theme and self._selected_theme.word_lists:
            for wl in self._selected_theme.word_lists:
                self.difficulty_combo.addItem(wl.difficulty.capitalize(), wl.difficulty)
        
        # Seleccionar la dificultad por defecto si existe y es válida
        if self._selected_theme and self._selected_theme.metadata:
            default_difficulty = self._selected_theme.metadata.get("default_difficulty")
            if default_difficulty:
                index = self.difficulty_combo.findData(default_difficulty.lower())
                if index != -1:
                    self.difficulty_combo.setCurrentIndex(index)
                    self._selected_difficulty = default_difficulty.lower()
        
        # Conectar el cambio de dificultad para actualizar _selected_difficulty
        self.difficulty_combo.currentIndexChanged.connect(self._update_selected_difficulty)

    def _update_selected_difficulty(self) -> None:
        self._selected_difficulty = self.difficulty_combo.currentData()


    def _handle_generate_request(self) -> None:
        # Si hay un tema seleccionado, pre-rellenar el ConfigDialog
        initial_config = None
        if self._selected_theme and self._selected_difficulty:
            try:
                initial_config = self._create_puzzle_config_from_theme(
                    self._selected_theme, self._selected_difficulty
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Error de Configuración", str(exc))
                return
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Error al preparar configuración del tema: {exc}")
                return

        dialog = ConfigDialog(self, base_config=initial_config)
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
        self.action_regenerate.setEnabled(True)
        self._update_hint_banner(None)
        self._update_editor_state()
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
        self.action_regenerate.setEnabled(True)
        self._update_hint_banner(None)
        self._update_editor_state()

        if config_id:
            self._last_config_id = config_id
            self.statusBar().showMessage(f"Puzzle guardado con ID {config_id}.", 5000)
        else:
            self.statusBar().showMessage("Puzzle generado.", 5000)

    def open_temas_module(self) -> None:
        dialog = TemasDialog(self)
        dialog.exec()
        # Recargar temas y categorías después de cerrar el diálogo de gestión
        self._load_categories_into_combo()

    def open_diagramacion_module(self) -> None:
        self._ensure_editor_docks()
        self.stack.setCurrentWidget(self.editor_page)
        if self.current_result is None:
            self._update_hint_banner(
                "Genera un puzzle manual, desde un tema o con el generador rápido."
            )
        self._set_editor_mode(True)
        self._update_editor_state()

    def open_quick_generator(self) -> None:
        defaults = self._default_generation_params()
        preset_words = None
        if self._selected_theme and self._selected_difficulty:
            try:
                theme_config = self._create_puzzle_config_from_theme(
                    self._selected_theme, self._selected_difficulty
                )
                preset_words = theme_config.words
                defaults = {
                    "rows": theme_config.rows,
                    "cols": theme_config.cols,
                    "difficulty": theme_config.difficulty,
                }
            except ValueError as exc:
                QMessageBox.warning(self, "Tema incompleto", str(exc))
                return
            except Exception as exc:
                QMessageBox.critical(self, "Tema inválido", str(exc))
                return

        dialog = QuickGeneratorDialog(
            self,
            preset_words=preset_words,
            default_rows=defaults["rows"],
            default_cols=defaults["cols"],
            default_difficulty=defaults["difficulty"],
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            config = dialog.build_config()
        except Exception as exc:  # pylint: disable=broad-except
            show_validation_error(self, str(exc))
            return
        self._generate_and_display(config, persist=dialog.should_persist())

    def _handle_generate_from_selected_theme(self) -> None:
        if not self._selected_theme or not self._selected_difficulty:
            QMessageBox.information(
                self,
                "Selección Incompleta",
                "Por favor, selecciona un Tema y una Dificultad para generar.",
            )
            return
        
        try:
            config = self._create_puzzle_config_from_theme(
                self._selected_theme, self._selected_difficulty
            )
            self._generate_and_display(config, persist=True)
        except ValueError as exc:
            QMessageBox.warning(self, "Error de Configuración", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error al generar desde tema: {exc}")

    def _create_puzzle_config_from_theme(self, theme: Theme, difficulty: str) -> PuzzleConfig:
        word_list_for_difficulty = next(
            (wl for wl in theme.word_lists if wl.difficulty == difficulty),
            None,
        )
        if not word_list_for_difficulty or not word_list_for_difficulty.words:
            raise ValueError(f"El tema '{theme.name}' no tiene palabras para la dificultad '{difficulty}'.")

        words = word_list_for_difficulty.words
        
        # Obtener parámetros de configuración por defecto del tema o de la configuración global
        cfg = load_config()
        default_rows, default_cols = cfg.get("grid", {}).get("default_size", (15, 15))
        
        rows = theme.metadata.get("default_rows", default_rows)
        cols = theme.metadata.get("default_cols", default_cols)
        alphabet = theme.metadata.get("default_alphabet", cfg.get("alphabet", "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"))
        directions = theme.metadata.get("default_directions", PuzzleConfig.DEFAULT_DIRECTIONS)

        return PuzzleConfig(
            theme_id=theme.id,
            words=words,
            rows=rows,
            cols=cols,
            difficulty=difficulty,
            alphabet=alphabet,
            directions=directions,
        )

    def _default_generation_params(self) -> dict:
        # Esta función ya no es tan relevante con el nuevo sistema de temas,
        # pero se mantiene por si se usa en otros contextos o para la generación manual.
        if self.current_config:
            return {
                "rows": self.current_config.rows,
                "cols": self.current_config.cols,
                "difficulty": self.current_config.difficulty,
            }
        cfg = load_config()
        rows, cols = cfg.get("grid", {}).get("default_size", (15, 15))
        difficulty = "medio" # Default en español
        # Asegurarse de que la dificultad por defecto sea una de las permitidas
        if difficulty not in PuzzleConfig.ALLOWED_DIFFICULTIES:
            difficulty = list(PuzzleConfig.ALLOWED_DIFFICULTIES)[0] # Tomar la primera si la por defecto no es válida
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
        if self.properties_panel is None:
            return
        self.properties_panel.update_from_items(self.scene.selectedItems())


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
