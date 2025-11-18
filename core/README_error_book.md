# Libro de Errores Inteligente

El Libro de Errores es un sistema de depuración avanzado que combina logging tradicional con técnicas de Machine Learning para proporcionar un manejo de errores más inteligente y sugerencias automáticas de solución.

## Características

### 1. Captura Inteligente de Errores
- Captura automática de excepciones en puntos críticos de la aplicación
- Análisis de contexto para cada error
- Integración con el sistema de logging existente

### 2. Análisis con ML
- Utiliza algoritmos de similitud (difflib) para comparar errores con patrones conocidos
- Clasificación automática de tipos de error
- Sugerencias contextuales basadas en errores similares

### 3. Base de Conocimiento
El sistema incluye una base de conocimiento predefinida con soluciones para errores comunes:

- **ImportError**: Problemas de importación de módulos
- **PuzzleGenerationError**: Errores en la generación de puzzles
- **DatabaseError**: Problemas con la base de datos SQLite
- **FileNotFoundError**: Archivos no encontrados
- **ValueError**: Errores de conversión o validación

### 4. Estadísticas y Métricas
- Conteo de tipos de error
- Identificación del error más común
- Historial de errores recientes
- Sugerencias de mejora del sistema

## Uso

### Captura Automática
El sistema captura errores automáticamente en:
- Punto de entrada principal (`app_desktop.py`)
- Controladores de puzzle (`puzzle_controller.py`)
- Ventana principal (`main_window.py`)

### Consulta de Estadísticas
```bash
python app_desktop.py --error-stats
```

Esto muestra:
- Total de errores registrados
- Distribución por tipo
- Error más común
- Sugerencias de mejora
- Lista de errores recientes con sugerencias

### En Código
```python
from core.error_book import capture_exception

try:
    # Código que puede fallar
    risky_operation()
except Exception as exc:
    capture_exception(exc, {"context": "operation_name", "extra_data": value})
```

## Arquitectura

### Componentes Principales

1. **ErrorBook**: Clase principal que maneja la lógica de análisis
2. **ErrorEntry**: Representa una entrada individual de error
3. **Base de Conocimiento**: Diccionario de patrones y soluciones conocidas

### Integración con Logging
- Los errores se registran en `data/logs/app.log`
- Cada error incluye sugerencias automáticas
- Compatible con el sistema de logging existente

### ML Básico
Utiliza `difflib.SequenceMatcher` para:
- Comparar mensajes de error con patrones conocidos
- Calcular puntuaciones de similitud
- Proporcionar sugerencias relevantes

## Extensión

### Agregar Nuevos Patrones
Para agregar soporte para nuevos tipos de error:

```python
# En error_book.py, en _load_known_errors()
"NewErrorType": {
    "patterns": ["patron1", "patron2"],
    "solutions": ["Solución 1", "Solución 2"]
}
```

### Personalizar Sugerencias
Las sugerencias se pueden personalizar basándose en:
- Tipo de error
- Contexto proporcionado
- Patrón de similitud encontrado

## Beneficios

1. **Depuración Acelerada**: Sugerencias automáticas reducen tiempo de debugging
2. **Mejor UX**: Errores más informativos para usuarios
3. **Mantenimiento Proactivo**: Estadísticas ayudan a identificar problemas recurrentes
4. **Escalabilidad**: Fácil agregar nuevos tipos de error y soluciones

## Ejemplo de Salida

```
Total de errores: 5
Tipos de error:
 - ValueError: 3
 - ImportError: 2
Error más común: ValueError (3 veces)

Sugerencias de mejora:
 - Considerar agregar más validaciones de entrada
 - Revisar dependencias del proyecto

Errores recientes:
 - [2025-11-17T10:30:00] ValueError: invalid literal for int()
   Sugerencias: Verificar el tipo de datos esperado | Usar try-except para conversiones
```