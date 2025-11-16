# Generador de Sopas de Letras en Python

Un generador de sopas de letras (word search) con interfaz gráfica de usuario (GUI) para crear, editar y exportar puzzles personalizados. El proyecto permite a los usuarios configurar puzzles, generar grids automáticamente, editar layouts visualmente y exportar resultados.

## Características Principales

- **Generación Automática**: Algoritmo inteligente para colocar palabras en horizontal, vertical y diagonal.
- **Interfaz Gráfica**: Editor visual con Qt/PySide6 para diagramar y editar puzzles.
- **Configuración Personalizable**: Filas, columnas, lista de palabras, temas de colores.
- **Edición Visual**: Mover elementos, cambiar colores, zoom.
- **Exportación**: Guardar como imagen (PNG) o PDF.
- **Persistencia**: Guardar/cargar proyectos en base de datos SQLite.
- **Pruebas Unitarias**: Cobertura completa con pytest.

## Tecnologías y Librerías

Seleccionamos las mejores librerías para un desarrollo robusto, eficiente y mantenible:

- **GUI**: [PySide6](https://pypi.org/project/PySide6/) - Bindings de Qt6 para Python. Elegido por su estabilidad, widgets ricos y compatibilidad con Windows/Linux/Mac. Alternativa moderna a PyQt6, con licencia LGPL.
- **Modelos de Datos**: [Pydantic](https://pypi.org/project/pydantic/) - Validación y serialización de datos. Asegura tipos seguros y validaciones automáticas para configuraciones.
- **Manipulación de Grids**: [NumPy](https://pypi.org/project/numpy/) - Arrays eficientes para manejar la grid del puzzle. Acelera operaciones matriciales en la generación.
- **Base de Datos**: [SQLite](https://www.sqlite.org/) (built-in con sqlite3) - Ligera y sin servidor. Suficiente para persistencia local de proyectos.
- **Exportación a PDF**: [ReportLab](https://pypi.org/project/reportlab/) - Generación profesional de PDFs. Ideal para puzzles imprimibles.
- **Manipulación de Imágenes**: [Pillow](https://pypi.org/project/pillow/) - Procesamiento de imágenes para exportar grids como PNG.
- **Pruebas**: [pytest](https://pypi.org/project/pytest/) - Framework de testing simple y potente. Incluye fixtures y parametrización.
- **Empaquetado**: [PyInstaller](https://pypi.org/project/pyinstaller/) - Crea ejecutables standalone. Facilita distribución sin instalar Python.
- **Control de Versiones**: Git - Para colaboración y seguimiento de cambios.

## Instalación

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/yeuryalberto01/Generadorde_sopas_de_letas_en_python.git
   cd Generadorde_sopas_de_letas_en_python
   ```

2. **Crea un entorno virtual**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Instala dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

   (Si no existe `requirements.txt`, instala manualmente: `pip install PySide6 pydantic numpy reportlab pillow pytest pyinstaller`)

4. **Ejecuta la aplicación**:
   ```bash
   python app_desktop.py
   ```

## Uso

1. **Configurar Puzzle**: Abre el diálogo de configuración para ingresar filas, columnas, palabras y tema.
2. **Generar**: Usa el menú para crear la sopa de letras automáticamente.
3. **Editar**: Mueve palabras, cambia colores en el editor visual.
4. **Exportar**: Guarda como imagen o PDF desde el menú Archivo.
5. **Guardar/Cargar**: Persiste proyectos en la base de datos.

En la aplicación de escritorio encontrarás el menú `Puzzle`:

- **Generar nuevo...** abre un diálogo para definir filas, columnas, dificultad, palabras, alfabeto y direcciones soportadas. Tras validar los datos se invoca el backend real y, opcionalmente, se guarda el resultado en SQLite.
- **Regenerar último** vuelve a crear la sopa usando la última configuración aplicada, útil para experimentar con diferentes alfabetos o layouts sin volver a tipear la lista de palabras.
- **Abrir guardado...** muestra los puzzles almacenados recientemente (consultados desde SQLite) y permite cargar uno para seguir editando o exportarlo.
- `Archivo > Exportar imagen...` genera un PNG en alta resolución y `Archivo > Exportar a PDF` utiliza un exportador dedicado con QPrinter para conservar la página completa en PDF.

### Modo CLI y Persistencia

Mientras se completa la interfaz definitiva, puedes probar rápidamente el generador y la base de datos con los nuevos comandos:

- Generar un puzzle desde consola y guardarlo:

  ```bash
  python app_desktop.py --generate-cli --words=python,qt,widget,editor --rows=12 --cols=12
  ```

  Opcionalmente añade `--alphabet=ABCDEFGHIJKLMNÑOPQRSTUVWXYZ` o `--directions=E,W,N,S,NE,NW,SE,SW` para personalizar.

- Consultar los últimos puzzles guardados:

  ```bash
  python app_desktop.py --list-puzzles --limit=5
  ```

Ambos comandos utilizan `core.generator.generate_puzzle`, validan la configuración con Pydantic y almacenan el resultado en SQLite (`data/puzzles.db`).

## Plan de Desarrollo Paso a Paso

Para que cualquier programador pueda continuar el desarrollo, aquí el roadmap estructurado:

### Fase 1: Mejora del Backend (Generación de Puzzles)
1. **Implementar algoritmo de generación**:
   - Reemplazar placeholder en `core/generator.py`.
   - Usar NumPy para grid.
   - Lógica: Colocar palabras en direcciones aleatorias, evitar overlaps, rellenar con letras aleatorias.
   - Validar: Palabras caben en grid, no duplicadas.

2. **Validación de entrada**:
   - En `core/models.py`, agregar validadores Pydantic (longitud de palabras, dimensiones mín/máx).

3. **Persistencia en DB**:
   - Crear tablas en `core/db.py` para `PuzzleConfig` y `PuzzleResult`.
   - Funciones para guardar/cargar.

### Fase 2: Desarrollo del Frontend (Interfaz de Usuario)
4. **Agregar diálogo de configuración**:
   - Crear `diagramacion/config_dialog.py` con QSpinBox, QListWidget, QColorDialog.

5. **Integrar generación**:
   - Botón en `main_window.py` para llamar a `generate_puzzle` y actualizar escena.

6. **Mejorar edición visual**:
   - Agregar herramientas en `tools/` (zoom, selección múltiple).
   - Señales para actualizar posiciones en tiempo real.

7. **Diálogo de exportación**:
   - Usar Pillow/ReportLab en `diagramacion/export_dialog.py`.

### Fase 3: Integración Backend-Frontend
8. **Conectar configuración**:
   - Pasar datos de diálogo a backend.

9. **Actualizar escena dinámicamente**:
   - `PuzzleItem` muestra grid, `WordBoxItem` posiciones.

10. **Guardar/cargar proyectos**:
    - Menús para DB operations.

### Fase 4: Pruebas y Calidad
11. **Agregar pruebas unitarias**:
    - `tests/test_generator.py`: Pruebas de colocación de palabras.
    - `tests/test_ui.py`: Pruebas de widgets con pytest-qt.

12. **Pruebas de integración**:
    - Flujo completo con fixtures.

13. **Documentación**:
    - Docstrings en todos los métodos.
    - Actualizar este README.

### Fase 5: Finalización y Despliegue
14. **Empaquetado**:
    - `pyinstaller app_desktop.py --onefile` para exe.

15. **Optimizaciones**:
    - Manejo de errores, logging.

16. **Lanzamiento**:
    - Subir a PyPI, agregar releases en GitHub.

## Contribución

1. Forkea el repo.
2. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`.
3. Commit cambios: `git commit -m "Agrega nueva funcionalidad"`.
4. Push: `git push origin feature/nueva-funcionalidad`.
5. Abre un Pull Request.

Sigue PEP 8, agrega tests para nuevos códigos.

## Licencia

MIT License - Ver `LICENSE` para detalles.

## Contacto

Yeury Alberto - [GitHub](https://github.com/yeuryalberto01)

¡Contribuye y mejora este generador de sopas de letras!
