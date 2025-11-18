"""Desktop entry point and CLI helpers for the word-search generator."""

from __future__ import annotations

import argparse
import io
import logging
import logging.handlers
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable, List, Sequence

from PySide6 import QtWidgets  # pylint: disable=import-error
from PySide6.QtCore import qInstallMessageHandler, QtMsgType  # pylint: disable=import-error,no-name-in-module,no-name-in-module

from core import (
    generate_puzzle,
    init_db,
    list_recent_puzzles,
    save_puzzle,
)
from core.error_book import capture_exception, get_error_stats, get_improvement_suggestions
from core.models import PuzzleConfig
from diagramacion.main_window import MainWindow

# Configurar logging
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Crear subdirectorios para organizar logs
DAILY_LOG_DIR = LOG_DIR / "daily"
ERROR_LOG_DIR = LOG_DIR / "errors"
QT_LOG_DIR = LOG_DIR / "qt"
for dir_path in [DAILY_LOG_DIR, ERROR_LOG_DIR, QT_LOG_DIR]:
    dir_path.mkdir(exist_ok=True)

# Formatter común
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Handler para logs diarios (rotación por día)
daily_handler = logging.handlers.TimedRotatingFileHandler(
    DAILY_LOG_DIR / "app.log",
    when="midnight",  # Rotar a medianoche
    interval=1,
    backupCount=30,  # Mantener 30 días
    encoding="utf-8",
)
daily_handler.setFormatter(formatter)
daily_handler.setLevel(logging.INFO)

# Handler para errores (rotación por tamaño)
error_handler = RotatingFileHandler(
    ERROR_LOG_DIR / "errors.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10,
    encoding="utf-8",
)
error_handler.setFormatter(formatter)
error_handler.setLevel(logging.ERROR)

# Handler específico para Qt
qt_handler = RotatingFileHandler(
    QT_LOG_DIR / "qt.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
qt_handler.setFormatter(formatter)

# Configurar root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # Nivel bajo para capturar todo
root_logger.addHandler(daily_handler)
root_logger.addHandler(error_handler)

# Logger específico para Qt ya está configurado arriba

logger = logging.getLogger(__name__)
logger.info("Aplicación iniciada")


class StderrCapture(io.StringIO):
    """Captura stderr y lo redirige al logger."""

    # Remove useless __init__ method that only calls super()
    # The default StringIO.__init__() is sufficient


def qt_message_handler(mode: QtMsgType, context, message: str) -> None:  # pylint: disable=unused-argument
    """Handler para redirigir mensajes de Qt al logger de Python."""
    level = logging.WARNING
    if mode == QtMsgType.QtDebugMsg:
        level = logging.DEBUG
    elif mode == QtMsgType.QtInfoMsg:
        level = logging.INFO
    elif mode == QtMsgType.QtWarningMsg:
        level = logging.WARNING
    elif mode == QtMsgType.QtCriticalMsg:
        level = logging.ERROR
    elif mode == QtMsgType.QtFatalMsg:
        level = logging.CRITICAL

    # Crear logger específico para Qt
    qt_logger = logging.getLogger("Qt")
    qt_logger.log(level, message)


def build_parser() -> argparse.ArgumentParser:  # pylint: disable=missing-function-docstring
    parser = argparse.ArgumentParser(
        description="Generador de sopas de letras con GUI o modo CLI.",
    )
    parser.add_argument(
        "--generate-cli",
        action="store_true",
        help="Genera una sopa desde CLI y la guarda en SQLite (requiere --words).",
    )
    parser.add_argument(
        "--interactive-cli",
        action="store_true",
        help="Inicia un asistente paso a paso en la terminal.",
    )
    parser.add_argument(
        "--words",
        type=str,
        help="Lista de palabras separadas por comas (ej. uno,dos,tres).",
    )
    parser.add_argument("--rows", type=int, default=15, help="Número de filas del puzzle.")
    parser.add_argument("--cols", type=int, default=15, help="Número de columnas del puzzle.")
    parser.add_argument(
        "--difficulty",
        type=str,
        default="medio",
        help="Dificultad (fácil|medio|difícil).",
    )
    parser.add_argument(
        "--alphabet",
        type=str,
        default=None,
        help="Alfabeto personalizado para rellenar celdas vacías.",
    )
    parser.add_argument(
        "--directions",
        type=str,
        default=None,
        help="Direcciones permitidas separadas por comas (E,W,N,S,NE,NW,SE,SW).",
    )
    parser.add_argument(
        "--list-puzzles",
        action="store_true",
        help="Lista los últimos puzzles guardados y termina.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Límite para --list-puzzles.",
    )
    parser.add_argument(
        "--error-stats",
        action="store_true",
        help="Muestra estadísticas de errores y sugerencias de mejora.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:  # pylint: disable=missing-function-docstring
    """Initialize the database and launch the CLI handler or GUI."""
    args = build_parser().parse_args(argv)
    init_db()
    logger.info("Base de datos inicializada")

    if args.list_puzzles:
        _print_recent(args.limit)
        return 0

    if args.error_stats:
        _print_error_stats()
        return 0

    if args.generate_cli:
        _generate_cli(args)
        return 0

    if args.interactive_cli:
        try:
            from cli import run_interactive_cli  # pylint: disable=import-outside-toplevel
        except ImportError as exc:  # pragma: no cover
            raise SystemExit(str(exc)) from exc
        run_interactive_cli(loop=True)
        return 0

    # Instalar handler para capturar mensajes de Qt
    qInstallMessageHandler(qt_message_handler)

    # Capturar stderr para mensajes de Qt que no pasan por el message handler
    stderr_capture = StderrCapture()
    sys.stderr = stderr_capture

    app = QtWidgets.QApplication(  # pylint: disable=c-extension-no-member
        sys.argv if argv is None else list(argv)
    )
    window = MainWindow()
    window.show()
    logger.info("Interfaz gráfica iniciada")
    return app.exec()


def _generate_cli(args: argparse.Namespace) -> None:
    logger.info("Generando puzzle desde CLI con palabras: %s", args.words)
    if not args.words:
        raise SystemExit("--generate-cli requiere --words=uno,dos,tres")
    word_list = _split_csv(args.words)
    if not word_list:
        raise SystemExit("Debe proporcionar al menos una palabra válida.")

    config_kwargs = {
        "words": word_list,
        "rows": args.rows,
        "cols": args.cols,
        "difficulty": args.difficulty,
    }
    if args.alphabet:
        config_kwargs["alphabet"] = args.alphabet
    if args.directions:
        config_kwargs["directions"] = [
            d.strip().upper() for d in args.directions.split(",") if d.strip()
        ]
    config = PuzzleConfig(**config_kwargs)
    logger.info("Configuración del puzzle: %s", config)
    result = generate_puzzle(config)
    logger.info(
        "Puzzle generado exitosamente, %s palabras colocadas",
        len(result.positions),
    )
    config_id = save_puzzle(config, result)
    logger.info("Puzzle guardado con ID %s", config_id)

    print(f"Puzzle guardado con ID {config_id} (dificultad {config.difficulty})")
    _print_grid(result.grid)
    print("Palabras colocadas:")
    for pos in result.positions:
        print(f" - {pos.word}: {pos.start} -> {pos.end} ({pos.direction})")


def _print_error_stats() -> None:
    stats = get_error_stats()
    if stats["total_errors"] == 0:
        print("No hay errores registrados.")
        return

    print(f"Total de errores: {stats['total_errors']}")
    print("Tipos de error:")
    for error_type, count in stats["error_types"].items():
        print(f" - {error_type}: {count}")

    if stats.get("most_common"):
        most_common, count = stats["most_common"]
        print(f"Error más común: {most_common} ({count} veces)")

    print("\nSugerencias de mejora:")
    suggestions = get_improvement_suggestions()
    if suggestions:
        for suggestion in suggestions:
            print(f" - {suggestion}")
    else:
        print(" - No hay sugerencias específicas disponibles.")

    print("\nErrores recientes:")
    for error in stats.get("recent_errors", []):
        print(f" - [{error['timestamp']}] {error['error_type']}: {error['message']}")
        if error['suggestions']:
            print(f"   Sugerencias: {' | '.join(error['suggestions'][:2])}")


def _print_recent(limit: int) -> None:
    rows = list_recent_puzzles(limit=limit)
    if not rows:
        print("No hay puzzles guardados todavía.")
        return
    print("Puzzles guardados recientemente:")
    for config_id, difficulty, rows_count, cols_count, created_at in rows:
        print(
            f" - ID {config_id}: {rows_count}x{cols_count}, "
            f"dificultad {difficulty}, creado {created_at}"
        )


# Removed duplicate _print_error_stats() function


def _split_csv(raw: str) -> List[str]:
    return [token.strip() for token in raw.split(",") if token.strip()]


def _print_grid(grid: Iterable[Iterable[str]]) -> None:
    for row in grid:
        line = " ".join(letter or "." for letter in row)
        print(f"  {line}")


if __name__ == "__main__":
    # Use more specific exception types instead of broad Exception
    try:
        sys.exit(main())
    except (SystemExit, KeyboardInterrupt):
        # These are expected exceptions, let them propagate naturally
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Capturar errores no manejados con el libro de errores
        capture_exception(exc, {"context": "main_entry_point"})
        logger.critical("Error crítico no manejado: %s", exc, exc_info=True)
        print(f"Error crítico: {exc}")
        print("Revisa los logs para más detalles y sugerencias.")
        sys.exit(1)
