"""Supervisor gate — LLM evaluates stage output against the spec."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from oneshot.agents.base import _extract_json
from oneshot.config import OneshotConfig
from oneshot.models import get_llm
from oneshot.prompts.supervisor import GATE_EVALUATION
from oneshot.schemas.quality import GateResult


def create_gate_node(config: OneshotConfig, stage_name: str, stage_key: str):
    """Create a supervisor gate node for a specific stage.

    Args:
        config: Oneshot configuration
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

        response = llm.invoke(messages)
        result = _extract_json(response.content)

        # Validate with Pydantic
        gate_result = GateResult.model_validate(result)

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
