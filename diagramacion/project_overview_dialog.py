"""Dialogo que resume los componentes principales del proyecto."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QTextBrowser,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROJECT_STRUCTURE: List[Dict[str, Any]] = [
    {
        "name": "README.md",
        "description": (
            "Resumen del proyecto, dependencias y comandos para lanzar la interfaz."
        ),
        "details": (
            "Contiene la guía rápida para crear un entorno virtual, instalar "
            "dependencias básicas y ejecutar `python app_desktop.py`."
        ),
    },
    {
        "name": "app_desktop.py",
        "description": "Punto de entrada: CLI + GUI. Permite generar puzzles y abrir la ventana principal.",
        "details": (
            "Crea la QApplication de PySide6, llama a `core.init_db()` para garantizar "
            "la base de datos y muestra `MainWindow`. Como alternativa acepta argumentos "
            "CLI (`--generate-cli`, `--list-puzzles`) que usan el backend sin abrir la GUI."
        ),
    },
    {
        "name": "core/",
        "description": "Núcleo lógico: configuración, base de datos, modelos y layouts.",
        "children": [
            {
                "name": "config.py",
                "description": "Carga `config.json` (si existe) y fusiona con valores por defecto.",
            },
            {
                "name": "db.py",
                "description": "Administra `data/puzzles.db`: crea tablas y guarda/carga puzzles generados.",
            },
            {
                "name": "generator.py",
                "description": "Motor real que ubica palabras con NumPy, respetando direcciones configurables.",
            },
            {
                "name": "models.py",
                "description": "Modelos Pydantic para la configuración, posiciones y resultado del puzzle.",
            },
            {
                "name": "layouts.py",
                "description": "Layouts predefinidos que ubican puzzle y caja de palabras en la página.",
            },
        ],
    },
    {
        "name": "diagramacion/",
        "description": "Interfaz PySide6: escena, vista, items gráficos y controladores.",
        "children": [
            {
                "name": "main_window.py",
                "description": "Ventana principal con menús para centrar la página o salir.",
            },
            {
                "name": "scene.py",
                "description": "Construye la escena, crea PageItem/PuzzleItem/WordBoxItem y aplica layout.",
            },
            {
                "name": "config_dialog.py",
                "description": "Diálogo Qt para configurar filas, columnas, palabras y direcciones antes de generar.",
            },
            {
                "name": "load_puzzle_dialog.py",
                "description": "Listado de puzzles guardados en SQLite para volver a cargarlos desde la GUI.",
            },
            {
                "name": "view.py",
                "description": "QGraphicsView personalizado con zoom y paneo con el botón central.",
            },
            {
                "name": "items/",
                "description": "Elementos gráficos individuales (página, puzzle, wordbox, etc.).",
            },
            {
                "name": "panels/",
                "description": "Paneles dockeables como el de propiedades de selección.",
            },
            {
                "name": "temas_dialog.py",
                "description": "Diálogo dedicado para crear, renombrar y borrar temas y sus palabras.",
            },
            {
                "name": "controllers/",
                "description": "Controladores como `LayoutController` que mantienen los márgenes.",
            },
        ],
    },
    {
        "name": "data/ y media/",
        "description": "Carpetas utilitarias: datos persistentes y recursos gráficos.",
        "details": (
            "La carpeta `data/` se crea automáticamente (contiene `puzzles.db`). "
            "`media/` está preparada para imágenes o plantillas futuras."
        ),
    },
]


class ProjectOverviewDialog(QDialog):
    """Muestra un árbol con los archivos/carpetas clave y detalles contextuales."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resumen del proyecto")
        self.resize(800, 500)
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)

        self.tree = QTreeWidget(splitter)
        self.tree.setHeaderLabels(["Elemento", "Descripción"])
        self.tree.itemSelectionChanged.connect(self._handle_selection_changed)

        self.detail_view = QTextBrowser(splitter)
        self.detail_view.setOpenExternalLinks(True)
        self.detail_view.setReadOnly(True)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        self._readme_html = self._load_readme_html()
        self._populate_tree()
        self.tree.expandAll()
        self.detail_view.setHtml(self._readme_html)

    def _populate_tree(self) -> None:
        self.tree.clear()
        for node in PROJECT_STRUCTURE:
            self._add_node(node, None)

    def _add_node(self, node: Dict[str, Any], parent_item: QTreeWidgetItem | None) -> QTreeWidgetItem:
        cols = [node.get("name", "Elemento"), node.get("description", "")]
        if parent_item is None:
            item = QTreeWidgetItem(self.tree, cols)
        else:
            item = QTreeWidgetItem(parent_item, cols)
        item.setData(0, Qt.ItemDataRole.UserRole, node)
        for child in node.get("children", []):
            self._add_node(child, item)
        return item

    def _handle_selection_changed(self) -> None:
        selected = self.tree.selectedItems()
        if not selected:
            self.detail_view.setHtml(self._readme_html)
            return
        node = selected[0].data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(node, dict):
            self.detail_view.setHtml(self._readme_html)
            return

        details = node.get("details") or node.get("description") or ""
        name = node.get("name", "Elemento")
        html = f"<h2>{escape(name)}</h2><p>{escape(details)}</p>"
        self.detail_view.setHtml(html)

    def _load_readme_html(self) -> str:
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            text = readme_path.read_text(encoding="utf-8")
            return f"<h2>README.md</h2><pre>{escape(text)}</pre>"
        return "<p>No se encontró README.md en el proyecto.</p>"


__all__ = ["ProjectOverviewDialog"]
