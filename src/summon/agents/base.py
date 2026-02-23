"""Agent factory — creates LangGraph node functions from config."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

from langchain_core.messages import HumanMessage, SystemMessage

from summon.config import SummonConfig
from summon.models import get_llm


def create_agent_node(
    config: SummonConfig,
    model_key: str,
    system_prompt: str,
    user_prompt_template: str,
    output_key: str,
    temperature: float = 0.0,
):
    """Factory that returns a LangGraph node function.

    The returned function:
    1. Formats the user prompt with state values
    2. Calls the configured LLM
    3. Parses JSON output
    4. Returns {output_key: parsed_result}
    """
    max_retries = 5

    def node(state: dict[str, Any]) -> dict[str, Any]:
        model_name = config.get_model(model_key)
        llm = get_llm(model_name, temperature=temperature)

        # Always use safe formatting
        safe_state = _make_safe_state(state)
        user_prompt = user_prompt_template.format_map(_DefaultDict(safe_state))

        messages = [
            SystemMessage(content=system_prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanation, just the JSON object."),
            HumanMessage(content=user_prompt),
        ]

        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                time.sleep(min(2 ** (attempt - 1), 30))

            try:
                response = llm.invoke(messages)
                content = response.content
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM call failed for %s (attempt %d/%d): %s",
                    model_key, attempt, max_retries, exc,
                )
                continue

            try:
                parsed = _extract_json(content)
                return {output_key: parsed}
            except ValueError as exc:
                last_error = exc
                snippet = (content or "")[:200]
                logger.warning(
                    "JSON parse failed for %s (attempt %d/%d): %s — response started with: %s",
                    model_key, attempt, max_retries, exc, snippet,
                )

        # All retries exhausted — return empty result so the pipeline can
        # continue (downstream nodes handle missing data gracefully).
        logger.error(
            "All %d retries exhausted for %s. Returning empty result. Last error: %s",
            max_retries, model_key, last_error,
        )
        return {output_key: {}}

    return node


def create_structured_agent_node(
    config: SummonConfig,
    model_key: str,
    system_prompt: str,
    user_prompt_template: str,
    output_key: str,
    output_schema: type,
    temperature: float = 0.0,
):
    """Factory that returns a node using structured output (with_structured_output)."""
    def node(state: dict[str, Any]) -> dict[str, Any]:
        model_name = config.get_model(model_key)
        llm = get_llm(model_name, temperature=temperature)
        structured_llm = llm.with_structured_output(output_schema)

        safe_state = _make_safe_state(state)
        user_prompt = user_prompt_template.format_map(_DefaultDict(safe_state))

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        result = structured_llm.invoke(messages)
        if hasattr(result, 'model_dump'):
            return {output_key: result.model_dump()}
        return {output_key: result}

    return node


def _make_safe_state(state: dict[str, Any]) -> dict[str, str]:
    """Convert state values to strings safe for prompt formatting."""
    safe = {}
    for k, v in state.items():
        if isinstance(v, (dict, list)):
            safe[k] = json.dumps(v, indent=2)
        else:
            safe[k] = str(v)
    return safe


def _fix_json_string(text: str) -> str:
    """Attempt to fix common JSON issues from LLMs."""
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Fix single quotes → double quotes (naive but handles most cases)
    # Only do this if there are no double quotes at all
    if '"' not in text and "'" in text:
        text = text.replace("'", '"')
    return text


def _fix_newlines_in_strings(text: str) -> str:
    """Escape literal newlines inside JSON string values.

    LLMs (especially via proxies) often return JSON with literal newlines
    inside string values instead of \\n escape sequences. This is invalid
    JSON but very common.
    """
    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
            continue
        if ch == '\\' and in_string:
            result.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue
        if in_string and ch == '\n':
            result.append('\\n')
            continue
        if in_string and ch == '\r':
            result.append('\\r')
            continue
        if in_string and ch == '\t':
            result.append('\\t')
            continue
        result.append(ch)
    return ''.join(result)


def _try_parse_json(candidate: str) -> dict | list | None:
    """Try to parse JSON with progressive repair strategies."""
    for repair in [lambda t: t, _fix_json_string, _fix_newlines_in_strings,
                   lambda t: _fix_json_string(_fix_newlines_in_strings(t))]:
        try:
            return json.loads(repair(candidate))
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _extract_json(text: str) -> dict | list:
    """Extract JSON from LLM response text, with repair attempts."""
    text = text.strip()

    # Remove control characters (except \n, \r, \t) that break JSON parsing
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Replace lone surrogates that can appear in LLM output
    text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from ```json code blocks — use last ``` as end marker
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            # Use rfind for the closing ``` since content may contain backticks
            end = text.rfind("```")
            if end > start:
                candidate = text[start:end].strip()
                parsed = _try_parse_json(candidate)
                if parsed is not None:
                    return parsed
            else:
                # No closing ``` — response was likely truncated; take the rest
                candidate = text[start:].strip()
                repaired = _repair_truncated_json(candidate)
                if repaired is not None:
                    logger.warning("Repaired truncated JSON from unclosed code block.")
                    return repaired
        except ValueError:
            pass

    # Strategy 3: Extract from ``` code blocks
    if "```" in text:
        try:
            start = text.index("```") + 3
            newline = text.index("\n", start)
            end = text.rfind("```")
            if end > newline:
                candidate = text[newline:end].strip()
                parsed = _try_parse_json(candidate)
                if parsed is not None:
                    return parsed
        except ValueError:
            pass

    # Strategy 4: Find JSON object/array boundaries
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        end_idx = text.rfind(end_char)
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            candidate = text[start_idx:end_idx + 1]
            parsed = _try_parse_json(candidate)
            if parsed is not None:
                return parsed

    # Strategy 5: Handle truncated JSON — try to repair by closing open structures
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        if start_idx != -1:
            candidate = text[start_idx:]
            repaired = _repair_truncated_json(candidate)
            if repaired is not None:
                logger.warning(
                    "Repaired truncated JSON (likely hit max_tokens). "
                    "Output may be incomplete — check for missing entries."
                )
                return repaired

    raise ValueError(f"Could not extract JSON from response: {text[:500]}...")


def _repair_truncated_json(text: str) -> dict | list | None:
    """Attempt to repair truncated JSON from LLM output hitting max_tokens.

    Strategy: progressively trim from the end and try closing brackets.
    For files arrays, try to salvage whatever complete file entries exist.
    """
    # Try to find the last complete entry in a files array by looking for
    # the last complete "content": "..." pattern
    # First, try just closing off open brackets
    for suffix in [
        '"}]}',       # close content string + file object + files array + root
        '"}\n]}',
        '"}]\n}',
        '\n"}]}',
        '}]}',        # close file object + files array + root
        ']}',         # close files array + root
        '}',          # close root
        ']',          # close array
    ]:
        try:
            return json.loads(text + suffix)
        except json.JSONDecodeError:
            continue

    # Try finding the last complete JSON object in a files array
    # Look for the last `}, {` or `}]` pattern and trim there
    last_complete = text.rfind('"}\n    }')
    if last_complete == -1:
        last_complete = text.rfind('"}')
    if last_complete > 0:
        candidate = text[:last_complete + 2]  # include the closing '"}'
        for suffix in [']}', ']\n}', '\n]}', '\n]\n}']:
            try:
                return json.loads(candidate + suffix)
            except json.JSONDecodeError:
                continue

    return None


class _DefaultDict(dict):
    """Dict that returns placeholder for missing keys during str.format_map."""
    def __missing__(self, key: str) -> str:
        return "(not available)"
