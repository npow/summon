"""LLM factory — returns a ChatModel by model name string."""

from __future__ import annotations

import logging
import os

from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)

_KEY_NAMES = {
    "claude": "ANTHROPIC_API_KEY",
    "gpt": "OPENAI_API_KEY",
    "o1": "OPENAI_API_KEY",
    "o3": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

# Default max_tokens per model family.  Override via SummonConfig if needed.
_DEFAULT_MAX_TOKENS: dict[str, int] = {
    "claude": 16384,
    "gpt": 16384,
    "o1": 16384,
    "o3": 16384,
}


def _check_api_key(model_name: str) -> None:
    """Raise a clear error if the required API key is missing."""
    for prefix, env_var in _KEY_NAMES.items():
        if model_name.startswith(prefix):
            if not os.environ.get(env_var):
                raise EnvironmentError(
                    f"Model '{model_name}' requires {env_var} to be set.\n"
                    f"  export {env_var}=your-key-here"
                )
            return


def get_llm(
    model_name: str,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """Create an LLM instance by model name with automatic retry.

    Supports:
      - claude-* → langchain_anthropic.ChatAnthropic
      - gpt-* / o1-* / o3-* → langchain_openai.ChatOpenAI
      - gemini-* → langchain_google_genai.ChatGoogleGenerativeAI

    All returned models are wrapped with retry logic (3 attempts,
    exponential backoff) to survive transient API errors.
    """
    _check_api_key(model_name)

    # Resolve max_tokens from explicit arg or per-family default
    if max_tokens is None:
        for prefix, default in _DEFAULT_MAX_TOKENS.items():
            if model_name.startswith(prefix):
                max_tokens = default
                break

    if model_name.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=model_name, temperature=temperature, max_tokens=max_tokens or 16384,
        )
    elif model_name.startswith("gpt") or model_name.startswith("o1") or model_name.startswith("o3"):
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=model_name, temperature=temperature, max_tokens=max_tokens or 16384,
        )
    elif model_name.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unknown model prefix: {model_name}")

    return llm.with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )
