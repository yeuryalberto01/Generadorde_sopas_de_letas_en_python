from .config import load_config
from .generator import generate_puzzle, PuzzleGenerationError
from .db import init_db, list_recent_puzzles, load_puzzle, save_puzzle
from .lexicon import WordValidationResult, validate_word
from .themes import (
    # Category Management
    create_category,
    list_categories,
    update_category,
    delete_category,
    # Theme Management
    create_theme,
    get_theme,
    list_themes,
    update_theme_details,
    update_theme_metadata,
    delete_theme,
    # Word List Management
    add_or_update_word_list,
    get_word_list,
    delete_word_list,
)
from . import models, layouts

__all__ = [
    "load_config",
    "generate_puzzle",
    "PuzzleGenerationError",
    "init_db",
    "save_puzzle",
    "load_puzzle",
    "list_recent_puzzles",
    "validate_word",
    "WordValidationResult",
    # Category Management
    "create_category",
    "list_categories",
    "update_category",
    "delete_category",
    # Theme Management
    "create_theme",
    "get_theme",
    "list_themes",
    "update_theme_details",
    "update_theme_metadata",
    "delete_theme",
    # Word List Management
    "add_or_update_word_list",
    "get_word_list",
    "delete_word_list",
    "models",
    "layouts",
]
