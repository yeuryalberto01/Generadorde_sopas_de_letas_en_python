from .models import PuzzleConfig, PuzzleResult, WordPosition


def generate_puzzle(config: PuzzleConfig) -> PuzzleResult:
    """
    Genera una sopa de letras en base a la configuración.
    POR AHORA: placeholder que devuelve una grilla vacía.

    Más adelante:
      - Implementar el algoritmo real (posición de palabras, relleno con letras aleatorias, etc.).
    """
    rows = config.rows
    cols = config.cols
    grid = [["" for _ in range(cols)] for _ in range(rows)]
    positions: list[WordPosition] = []
    return PuzzleResult(grid=grid, positions=positions)
