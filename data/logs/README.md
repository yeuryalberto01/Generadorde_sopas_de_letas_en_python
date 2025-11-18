# Sistema de Logging Mejorado

El sistema de logging ha sido optimizado para evitar saturación y proporcionar mejor organización de los logs.

## Estructura de Logs

```
data/logs/
├── daily/           # Logs diarios (rotación automática)
│   └── app.log      # Log principal diario
├── errors/          # Logs de errores (rotación por tamaño)
│   └── errors.log   # Solo mensajes de ERROR y superiores
├── qt/              # Logs específicos de Qt
│   └── qt.log       # Mensajes de Qt (warnings y superiores)
└── app.log          # Log legacy (para compatibilidad)
```

## Características

### 1. Rotación por Tiempo (Daily)
- **Archivo**: `daily/app.log`
- **Rotación**: Diaria a medianoche
- **Retención**: 30 días
- **Contenido**: Todos los niveles de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### 2. Rotación por Tamaño (Errors)
- **Archivo**: `errors/errors.log`
- **Rotación**: Cada 10MB
- **Retención**: 10 archivos
- **Contenido**: Solo ERROR y CRITICAL

### 3. Logs Especializados (Qt)
- **Archivo**: `qt/qt.log`
- **Rotación**: Cada 5MB
- **Retención**: 5 archivos
- **Contenido**: Mensajes específicos de Qt

## Ventajas

### Evita Saturación
- **Rotación automática**: Los archivos no crecen indefinidamente
- **Separación por tipo**: Errores no se mezclan con logs informativos
- **Limpieza automática**: Archivos antiguos se eliminan automáticamente

### Mejor Organización
- **Logs por fecha**: Fácil encontrar logs de días específicos
- **Separación por severidad**: Errores separados del flujo normal
- **Especialización**: Logs Qt separados del código Python

### Mantenimiento
- **Retención configurable**: Ajustable según necesidades
- **Compresión implícita**: Archivos rotados son más pequeños
- **Rendimiento**: Múltiples handlers no afectan performance

## Configuración

La configuración se encuentra en `app_desktop.py`. Parámetros ajustables:

```python
# Rotación diaria
daily_handler = logging.handlers.TimedRotatingFileHandler(
    DAILY_LOG_DIR / "app.log",
    when="midnight",      # 'midnight', 'H' (hora), 'D' (día)
    interval=1,           # Cada cuánto rotar
    backupCount=30,       # Días a mantener
)

# Rotación por tamaño
error_handler = RotatingFileHandler(
    ERROR_LOG_DIR / "errors.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10,             # Archivos a mantener
)
```

## Uso en Código

```python
import logging

logger = logging.getLogger(__name__)

# Logs normales van a daily/app.log
logger.info("Mensaje informativo")
logger.warning("Advertencia")

# Errores van a daily/app.log Y errors/errors.log
logger.error("Error importante")

# Logs Qt van a qt/qt.log
qt_logger = logging.getLogger("Qt")
qt_logger.warning("Mensaje de Qt")
```

## Monitoreo

### Ver logs recientes
```bash
# Logs diarios
tail -f data/logs/daily/app.log

# Solo errores
tail -f data/logs/errors/errors.log

# Logs Qt
tail -f data/logs/qt/qt.log
```

### Buscar en logs
```bash
# Errores de hoy
grep "ERROR" data/logs/daily/app.log

# Errores de un día específico
grep "ERROR" data/logs/daily/app.log.2025-11-15
```

### Estadísticas
```bash
# Contar errores por tipo
grep "ERROR" data/logs/errors/errors.log | cut -d' ' -f6 | sort | uniq -c
```

## Recomendaciones

1. **Monitoreo regular**: Revisar logs de errores semanalmente
2. **Limpieza manual**: Si es necesario, eliminar logs antiguos manualmente
3. **Backup**: Los logs importantes pueden copiarse a ubicaciones seguras
4. **Alertas**: Configurar alertas para errores críticos

## Compatibilidad

- **Backward compatible**: El archivo `app.log` legacy se mantiene
- **Múltiples formatos**: Soporta diferentes formatos de fecha/hora
- **Configurable**: Fácil cambiar configuración sin afectar código