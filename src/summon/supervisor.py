"""Supervisor gate — LLM evaluates stage output against the spec."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from summon.agents.base import _extract_json
from summon.config import SummonConfig
from summon.models import get_llm
from summon.prompts.supervisor import GATE_EVALUATION
from summon.schemas.quality import GateResult

logger = logging.getLogger(__name__)


def create_gate_node(config: SummonConfig, stage_name: str, stage_key: str):
    """Create a supervisor gate node for a specific stage.

    Args:
        config: Summon configuration
        stage_name: Human-readable stage name (e.g. "idea_refinement")
        stage_key: The state key containing the stage's output to evaluate
    """
    threshold = config.get_threshold(stage_name)

    def gate_node(state: dict[str, Any]) -> dict[str, Any]:
        spec = state.get("spec", {})
        stage_output = state.get(stage_key, {})

        # Get previous feedback if this is a retry
        gate_results = state.get("gate_results", [])
        previous_feedback = ""
        for gr in reversed(gate_results):
            if gr.get("stage") == stage_name and not gr.get("passed"):
                previous_feedback = gr.get("feedback", "")
                break

        # Format the evaluation prompt
        prompt_text = GATE_EVALUATION.format(
            spec=json.dumps(spec, indent=2) if isinstance(spec, dict) else str(spec),
            stage_name=stage_name,
            stage_output=json.dumps(stage_output, indent=2) if isinstance(stage_output, (dict, list)) else str(stage_output),
            previous_feedback=previous_feedback or "None",
            threshold=threshold,
        )

        model_name = config.get_model("supervisor")
        llm = get_llm(model_name)

        messages = [
            SystemMessage(content="You are a quality supervisor. Evaluate pipeline outputs strictly."),
            HumanMessage(content=prompt_text),
        ]

        max_retries = 5
        last_error: Exception | None = None
        result = None
        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                time.sleep(min(2 ** (attempt - 1), 30))
            try:
                response = llm.invoke(messages)
                result = _extract_json(response.content)
                break
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gate %s LLM/parse failed (attempt %d/%d): %s",
                    stage_name, attempt, max_retries, exc,
                )
        if result is None:
            raise last_error  # type: ignore[misc]

        # Validate with Pydantic
        gate_result = GateResult.model_validate(result)

        # Enforce threshold programmatically — don't trust LLM's pass/fail
        gate_result.passed = (
            gate_result.score >= threshold and gate_result.scope_creep < 0.3
        )

        # Track retries
        stage_retries = dict(state.get("stage_retries", {}))
        current_retries = stage_retries.get(stage_name, 0)

        if not gate_result.passed:
            stage_retries[stage_name] = current_retries + 1

        # Force pass if max retries exceeded
        if current_retries >= config.max_stage_retries:
            gate_result.passed = True
            gate_result.feedback += " [FORCE PASSED: max retries exceeded]"

        return {
            "gate_results": [gate_result.model_dump()],
            "stage_retries": stage_retries,
            "current_stage": stage_name,
        }

    return gate_node


def gate_passed(state: dict[str, Any]) -> str:
    """Conditional edge function: returns 'pass' or 'retry'."""
    gate_results = state.get("gate_results", [])
    if gate_results:
        latest = gate_results[-1]
        if latest.get("passed", False):
            return "pass"
    return "retry"
