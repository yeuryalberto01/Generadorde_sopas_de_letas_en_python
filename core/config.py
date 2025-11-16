from pathlib import Path
import json
from copy import deepcopy

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = DATA_DIR / "config.json"


DEFAULT_CONFIG = {
    "page": {
        "size": "letter",  # "letter" | "A4"
        "orientation": "portrait",
        "margins_mm": {
            "top": 15,
            "bottom": 15,
            "left": 15,
            "right": 15,
        },
    },
    "grid": {
        "sizes": [(10, 10), (15, 15), (20, 20)],
        "default_size": (15, 15),
    },
    "difficulty": ["easy", "medium", "hard"],
    "theme": {
        "background_color": "#2b2b2b",
        "page_color": "#ffffff",
        "grid_line_color": "#999999",
        "wordbox_border_color": "#444444",
    },
}


def load_config() -> dict:
    cfg = deepcopy(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            disk_cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for key, value in disk_cfg.items():
                cfg[key] = value
        except Exception:
            # Si hay error en el JSON, se usa solo DEFAULT_CONFIG
            pass
    return cfg
