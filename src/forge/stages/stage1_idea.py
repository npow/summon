"""Stage 1: Idea Refinement — Ambiguity detect → Self-clarify → Spec write → Validate."""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import StateGraph, END

from forge.agents.ambiguity import create_ambiguity_node
from forge.agents.spec_writer import create_clarify_node, create_spec_writer_node
from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage1 import SPEC_VALIDATOR
from forge.state import ForgeState


def _process_ambiguities(state: dict[str, Any]) -> dict[str, Any]:
    """Extract ambiguity list from the LLM response."""
    raw = state.get("ambiguities", {})
    if isinstance(raw, dict):
        ambiguities = raw.get("ambiguities", [])
    elif isinstance(raw, list):
        ambiguities = raw
    else:
        ambiguities = [str(raw)]
    return {"ambiguities": ambiguities}


def _process_clarifications(state: dict[str, Any]) -> dict[str, Any]:
    """Extract clarification list from the LLM response."""
    raw = state.get("clarifications", {})
    if isinstance(raw, dict):
        clarifications = raw.get("clarifications", [])
    elif isinstance(raw, list):
        clarifications = raw
    else:
        clarifications = [str(raw)]

    # Format ambiguities and clarifications as strings for spec writer
    return {
        "clarifications": clarifications,
    }


def _format_for_spec(state: dict[str, Any]) -> dict[str, Any]:
    """Prepare state for spec writer by formatting lists as text."""
    ambiguities = state.get("ambiguities", [])
    clarifications = state.get("clarifications", [])

    if isinstance(ambiguities, list):
        amb_text = "\n".join(f"- {a}" for a in ambiguities)
    else:
        amb_text = str(ambiguities)

    if isinstance(clarifications, list):
        clar_text = "\n".join(f"- {c}" for c in clarifications)
    else:
        clar_text = str(clarifications)

    return {
        "ambiguities": amb_text,
        "clarifications": clar_text,
    }


def _validate_spec(state: dict[str, Any]) -> dict[str, Any]:
    """Basic spec validation without LLM."""
    spec = state.get("spec", {})
    if isinstance(spec, dict):
        required_keys = {"project_name", "one_liner", "functional_requirements", "language", "package_type"}
        missing = required_keys - set(spec.keys())
        if missing:
            return {"error": f"Spec missing keys: {missing}"}
    return {}


def create_stage1_graph(config: ForgeConfig) -> StateGraph:
    """Build the Stage 1 subgraph."""
    graph = StateGraph(ForgeState)

    # Nodes
    graph.add_node("detect_ambiguities", create_ambiguity_node(config))
    graph.add_node("process_ambiguities", _process_ambiguities)
    graph.add_node("self_clarify", create_clarify_node(config))
    graph.add_node("process_clarifications", _process_clarifications)
    graph.add_node("format_for_spec", _format_for_spec)
    graph.add_node("write_spec", create_spec_writer_node(config))
    graph.add_node("validate_spec", _validate_spec)

    # Edges
    graph.set_entry_point("detect_ambiguities")
    graph.add_edge("detect_ambiguities", "process_ambiguities")
    graph.add_edge("process_ambiguities", "self_clarify")
    graph.add_edge("self_clarify", "process_clarifications")
    graph.add_edge("process_clarifications", "format_for_spec")
    graph.add_edge("format_for_spec", "write_spec")
    graph.add_edge("write_spec", "validate_spec")
    graph.add_edge("validate_spec", END)

    return graph
