"""friendbot package public API.

Importing this package ensures environment/loading and logging via config,
exposes a stable surface for common operations, and provides the package version.
"""

__version__ = "0.1.0"

# Ensure env and logging are initialized upon package import
from . import config as config  # noqa: F401

# Re-export commonly used configuration and prompts
from .config import (
    TELEGRAM_TOKEN,
    OPENROUTER_KEY,
    DATABASE_URL,
    FREE_LIMIT,
    SUB_DURATION_DAYS,
    MAX_HISTORY,
    SYSTEM_PROMPT_GIRL,
    SYSTEM_PROMPT_BOY,
)

# Re-export DB layer helpers
from .db import (
    init_db,
    get_user,
    set_persona,
    set_free_count,
    set_sub_expiry,
    has_active_sub,
    save_message,
    get_history,
    trim_history,
)

# Re-export AI client and persona prompt util
from .ai import GPT, get_persona_prompt

# Re-export UI helpers
from .ui import persona_keyboard

__all__ = [
    "__version__",
    # Config
    "TELEGRAM_TOKEN",
    "OPENROUTER_KEY",
    "DATABASE_URL",
    "FREE_LIMIT",
    "SUB_DURATION_DAYS",
    "MAX_HISTORY",
    "SYSTEM_PROMPT_GIRL",
    "SYSTEM_PROMPT_BOY",
    # DB
    "init_db",
    "get_user",
    "set_persona",
    "set_free_count",
    "set_sub_expiry",
    "has_active_sub",
    "save_message",
    "get_history",
    "trim_history",
    # AI
    "GPT",
    "get_persona_prompt",
    # UI
    "persona_keyboard",
]
