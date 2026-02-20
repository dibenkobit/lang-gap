"""Model registry and OpenRouter configuration."""

import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# display name → OpenRouter model ID
MODELS: dict[str, str] = {
    "claude-opus-4.6": "anthropic/claude-opus-4-6",
    "claude-sonnet-4.6": "anthropic/claude-sonnet-4-6",
    "gpt-5.2": "openai/gpt-5.2",
    "gpt-4.1": "openai/gpt-4.1",
    "gemini-2.5-pro": "google/gemini-2.5-pro-preview-06-05",
    "deepseek-r1": "deepseek/deepseek-r1",
}

MAX_CONCURRENT_PER_MODEL = 5
MAX_RETRIES = 3
