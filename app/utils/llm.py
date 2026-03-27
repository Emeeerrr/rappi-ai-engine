"""
OpenRouter LLM Client - Unified interface for LLM completions via OpenRouter.

Uses the openai library with OpenRouter's compatible API endpoint.
Provides retry logic, logging, and a simple chat_completion interface.
"""

import logging
import time

from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    DEFAULT_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_MAX_RETRIES,
)

logger = logging.getLogger(__name__)

_client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)


def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = LLM_TEMPERATURE,
    max_tokens: int = LLM_MAX_TOKENS,
) -> str:
    """Send a chat completion request to OpenRouter and return the response text.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        model: Model identifier (defaults to DEFAULT_MODEL from config).
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the response.

    Returns:
        The assistant's response text.

    Raises:
        RuntimeError: If all retry attempts are exhausted.
    """
    model = model or DEFAULT_MODEL
    last_error = None

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            logger.info("LLM request | model=%s | attempt=%d/%d", model, attempt, LLM_MAX_RETRIES)

            response = _client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            text = response.choices[0].message.content
            logger.info("LLM response | tokens=%s", response.usage)
            return text

        except RateLimitError as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning("Rate limited, retrying in %ds (attempt %d/%d)", wait, attempt, LLM_MAX_RETRIES)
            time.sleep(wait)

        except (APIError, APIConnectionError) as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning("API error: %s, retrying in %ds (attempt %d/%d)", e, wait, attempt, LLM_MAX_RETRIES)
            time.sleep(wait)

    raise RuntimeError(f"LLM request failed after {LLM_MAX_RETRIES} attempts: {last_error}")
