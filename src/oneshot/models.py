"""LLM factory — returns a ChatModel by model name string."""

from __future__ import annotations

import os
import sys

from langchain_core.language_models import BaseChatModel


_KEY_NAMES = {
    "claude": "ANTHROPIC_API_KEY",
    "gpt": "OPENAI_API_KEY",
    "o1": "OPENAI_API_KEY",
    "o3": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
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


def get_llm(model_name: str, temperature: float = 0.0) -> BaseChatModel:
    """Create an LLM instance by model name.

    Supports:
      - claude-* → langchain_anthropic.ChatAnthropic
      - gpt-* / o1-* / o3-* → langchain_openai.ChatOpenAI
      - gemini-* → langchain_google_genai.ChatGoogleGenerativeAI
    """
    _check_api_key(model_name)

    if model_name.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, temperature=temperature, max_tokens=16384)
    elif model_name.startswith("gpt") or model_name.startswith("o1") or model_name.startswith("o3"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, temperature=temperature, max_tokens=16384)
    elif model_name.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unknown model prefix: {model_name}")
