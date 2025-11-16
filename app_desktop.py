"""Desktop entry point and CLI helpers for the word-search generator."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, List, Sequence

from PySide6 import QtWidgets  # pylint: disable=import-error

from core import (
    generate_puzzle,
    init_db,
    list_recent_puzzles,
    save_puzzle,
)
from core.models import PuzzleConfig
from diagramacion.main_window import MainWindow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generador de sopas de letras con GUI o modo CLI.",
    )
    parser.add_argument(
        "--generate-cli",
        action="store_true",
        help="Genera una sopa desde CLI y la guarda en SQLite (requiere --words).",
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
        default="medium",
        help="Dificultad (easy|medium|hard).",
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Initialize the database and launch the CLI handler or GUI."""
    args = build_parser().parse_args(argv)
    init_db()

    if args.list_puzzles:
        _print_recent(args.limit)
        return 0

    if args.generate_cli:
        _generate_cli(args)
        return 0

    app = QtWidgets.QApplication(  # pylint: disable=c-extension-no-member
        sys.argv if argv is None else list(argv)
    )
    window = MainWindow()
    window.show()
    return app.exec()


def _generate_cli(args: argparse.Namespace) -> None:
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
    result = generate_puzzle(config)
    config_id = save_puzzle(config, result)

    print(f"Puzzle guardado con ID {config_id} (dificultad {config.difficulty})")
    _print_grid(result.grid)
    print("Palabras colocadas:")
    for pos in result.positions:
        print(f" - {pos.word}: {pos.start} -> {pos.end} ({pos.direction})")


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


def _split_csv(raw: str) -> List[str]:
    return [token.strip() for token in raw.split(",") if token.strip()]


def _print_grid(grid: Iterable[Iterable[str]]) -> None:
    for row in grid:
        line = " ".join(letter or "." for letter in row)
        print(f"  {line}")


if __name__ == "__main__":
    sys.exit(main())
