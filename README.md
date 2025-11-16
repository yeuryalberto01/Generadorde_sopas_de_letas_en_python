# Generador de sopas de letras en Python

Proyecto base para un generador de sopas de letras con núcleo lógico y un módulo de diagramación en PySide6.

## Requisitos

Se recomienda usar un entorno virtual y las dependencias básicas:

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
pip install pydantic PySide6
```

## Ejecución

Inicializa la base de datos y abre la interfaz de diagramación con:

```bash
python app_desktop.py
```

Se abrirá una ventana con la página, guías de margen, la zona de puzzle y la caja de palabras. Puedes hacer zoom con la rueda del ratón, desplazarte con el botón central y mover la caja de palabras para que el puzzle se reorganice automáticamente.

## Estructura

- `core/`: configuración, modelos Pydantic, motor de generación (placeholder) y preparación de SQLite.
- `diagramacion/`: editor de página en PySide6 con vista de zoom/pan, escena, ítems de página/puzzle/wordbox y control básico de layout.
- `data/`: carpeta de datos (se creará `puzzles.db` en tiempo de ejecución).
- `media/`: recursos gráficos (subcarpetas preparadas).
