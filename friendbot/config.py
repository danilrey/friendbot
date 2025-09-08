import os
import logging
from dotenv import load_dotenv

# Load environment and configure logging early
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

# Tokens and connection strings
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:0000@localhost:5432/friendbot")

# App limits and behavior
FREE_LIMIT = int(os.getenv("FREE_LIMIT", "5"))
SUB_DURATION_DAYS = int(os.getenv("SUB_DURATION_DAYS", "30"))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "10"))  # how many last messages to keep in context

# Default system prompts
SYSTEM_PROMPT_GIRL = (
    "Ты милая девушка, поддерживающая разговор. Будь доброй, позитивной, тактичной, без 18+."
)
SYSTEM_PROMPT_BOY = (
    "Ты умный и добрый парень, поддерживающий разговор. Будь дружелюбным, тактичным, без 18+."
)

