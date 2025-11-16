from dataclasses import dataclass
from typing import List, Literal


ZoneArea = Literal[
    "top",
    "bottom",
    "left",
    "right",
    "center",
]


@dataclass
class Zone:
    id: str  # ej. "puzzle", "wordbox"
    area: ZoneArea


@dataclass
class PageLayout:
    name: str
    zones: List[Zone]


DEFAULT_LAYOUTS: List[PageLayout] = [
    PageLayout(
        name="Puzzle arriba, palabras abajo",
        zones=[
            Zone(id="puzzle", area="top"),
            Zone(id="wordbox", area="bottom"),
        ],
    ),
    PageLayout(
        name="Palabras arriba, puzzle abajo",
        zones=[
            Zone(id="wordbox", area="top"),
            Zone(id="puzzle", area="bottom"),
        ],
    ),
    PageLayout(
        name="Puzzle izquierda, palabras derecha",
        zones=[
            Zone(id="puzzle", area="left"),
            Zone(id="wordbox", area="right"),
        ],
    ),
]
