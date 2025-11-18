"""CLI interactivo guiado para generar sopas de letras."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

try:
    from rich.console import Console
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.table import Table
    from rich import box
except ImportError as exc:  # pragma: no cover - dependencia opcional
    raise ImportError(
        "El modo CLI interactivo requiere la librería 'rich'. "
        "Instálala con 'pip install rich'."
    ) from exc

from core import generate_puzzle, save_puzzle
from core.models import PuzzleConfig, PuzzleResult

DEFAULT_ROWS, DEFAULT_COLS = 15, 15

DIFFICULTY_DIRECTIONS = {
    "fácil": ["E", "W", "N", "S"],
    "medio": PuzzleConfig.DEFAULT_DIRECTIONS,
    "difícil": PuzzleConfig.DEFAULT_DIRECTIONS,
}


def run_interactive_cli(loop: bool = False) -> None:
    """Inicia el asistente interactivo y controla su ciclo."""
    console = Console()
    console.print("[bold cyan]Bienvenido al generador interactivo de sopas de letras[/bold cyan]")
    again = True

    while again:
        config, persist_choice = obtener_configuracion_usuario(console)
        console.print("\n[bold]Generando sopa de letras...[/bold]")
        result = _generate_puzzle(console, config)
        if result is None:
            if not loop:
                break
            again = Confirm.ask("\n¿Intentar de nuevo?", default=True)
            continue

        mostrar_resultado(console, config, result)

        if persist_choice:
            config_id = save_puzzle(config, result)
            console.print(f"[green]Puzzle guardado con ID {config_id}[/green]")

        again = loop and Confirm.ask("\n¿Generar otra sopa?", default=False)
        if not loop:
            break


def obtener_configuracion_usuario(console: Console) -> Tuple[PuzzleConfig, bool]:
    """Solicita filas, columnas, palabras y dificultad al usuario."""
    rows = _prompt_dimension(console, "Número de filas", DEFAULT_ROWS)
    cols = _prompt_dimension(console, "Número de columnas", DEFAULT_COLS)
    words = _prompt_words(console, max(rows, cols))
    difficulty = _prompt_difficulty(console)
    persist_choice = Confirm.ask(
        "¿Quieres guardar automáticamente la sopa generada en la base de datos?",
        default=True,
    )
    config = PuzzleConfig(
        rows=rows,
        cols=cols,
        words=words,
        difficulty=difficulty,
        directions=DIFFICULTY_DIRECTIONS[difficulty],
    )
    return config, persist_choice


def _prompt_dimension(console: Console, label: str, default: int) -> int:
    """Valida un entero para filas o columnas."""
    while True:
        value = IntPrompt.ask(
            f"{label} [{PuzzleConfig.MIN_SIZE}-{PuzzleConfig.MAX_SIZE}]",
            default=default,
            show_default=True,
        )
        if PuzzleConfig.MIN_SIZE <= value <= PuzzleConfig.MAX_SIZE:
            return value
        console.print(
            f"[red]El valor debe estar entre {PuzzleConfig.MIN_SIZE} y {PuzzleConfig.MAX_SIZE}[/red]"
        )


def _prompt_words(console: Console, max_side: int) -> List[str]:
    """Pide palabras separadas por comas y valida su longitud."""
    while True:
        raw = Prompt.ask(
            "Ingresa las palabras separadas por comas",
            default="python,qt,widget",
            show_default=True,
        )
        words = [token.strip() for token in raw.split(",") if token.strip()]
        if not words:
            console.print("[red]Debes ingresar al menos una palabra.[/red]")
            continue
        longest = max(len(word) for word in words)
        if longest > max_side:
            console.print(
                f"[red]La palabra más larga tiene {longest} caracteres y no cabe "
                f"en una grilla de lado {max_side}. Ajusta filas/columnas o la palabra.[/red]"
            )
            continue
        return words


def _prompt_difficulty(console: Console) -> str:
    choices = list(DIFFICULTY_DIRECTIONS)
    default = "medio"
    while True:
        selection = Prompt.ask(
            f"Selecciona dificultad ({'/'.join(choices)})",
            default=default,
            show_default=True,
        ).strip().lower()
        if selection in choices:
            return selection
        console.print("[red]Dificultad inválida. Usa fácil/medio/difícil.[/red]")


def _generate_puzzle(console: Console, config: PuzzleConfig) -> PuzzleResult | None:
    """Genera la sopa y captura errores del backend."""
    try:
        return generate_puzzle(config)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]No se pudo generar el puzzle: {exc}[/red]")
    return None


def _render_grid(console: Console, grid: Sequence[Sequence[str]]) -> None:
    table = Table(box=box.SQUARE, show_header=False, pad_edge=False)
    size = len(grid[0]) if grid else 0
    for _ in range(size):
        table.add_column(justify="center")
    for row in grid:
        table.add_row(*[letter or " " for letter in row])
    console.print("\n[bold green]Resultado[/bold green]")
    console.print(table)


def _render_words(console: Console, words: Iterable[str]) -> None:
    """Imprime en lista las palabras objetivo."""
    console.print("\n[bold cyan]Palabras a buscar:[/bold cyan]")
    for word in words:
        console.print(f" • {word}")


def mostrar_resultado(console: Console, config: PuzzleConfig, result: PuzzleResult) -> None:
    """Renderiza la cuadrícula y palabras de un resultado."""
    _render_grid(console, result.grid)
    _render_words(console, config.words)
