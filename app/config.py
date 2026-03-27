"""
Global configuration - Environment variables, constants, and model definitions.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# --- API Keys ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# --- Default Model ---
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-20250514")

# --- Available Models for UI selector ---
AVAILABLE_MODELS = [
    {"id": "anthropic/claude-sonnet-4-20250514", "label": "Claude Sonnet 4.6"},
    {"id": "anthropic/claude-haiku-4-5-20251001", "label": "Haiku 4.5"},
    {"id": "openai/gpt-4o", "label": "GPT-4o"},
    {"id": "google/gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
    {"id": "meta-llama/llama-4-maverick", "label": "Llama 4 Maverick"},
]

# --- LLM Defaults ---
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 4096
LLM_MAX_RETRIES = 3

# --- Data Constants ---
WEEK_COLUMNS_METRICS = [
    "L8W_ROLL", "L7W_ROLL", "L6W_ROLL", "L5W_ROLL",
    "L4W_ROLL", "L3W_ROLL", "L2W_ROLL", "L1W_ROLL", "L0W_ROLL",
]
WEEK_COLUMNS_ORDERS = [
    "L8W", "L7W", "L6W", "L5W", "L4W", "L3W", "L2W", "L1W", "L0W",
]
