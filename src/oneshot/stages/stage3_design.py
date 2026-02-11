"""Stage 3: High-Level Design — Architect → Component splitter."""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import StateGraph, END

from oneshot.agents.architect import create_architect_node
from oneshot.agents.splitter import create_splitter_node
from oneshot.config import OneshotConfig
from oneshot.state import OneshotState


def _extract_components(state: dict[str, Any]) -> dict[str, Any]:
    """Extract component list from splitter result and HLD."""
    split_result = state.get("_split_result", {})
    hld = state.get("hld", {})

    # Prefer splitter's validated components, fall back to HLD's
    components = split_result.get("components", hld.get("components", []))
    return {"components": components}


def _format_hld_for_splitter(state: dict[str, Any]) -> dict[str, Any]:
    """Format HLD as string for the splitter prompt."""
    hld = state.get("hld", {})
    return {"hld": hld}


def create_stage3_graph(config: OneshotConfig) -> StateGraph:
    """Build the Stage 3 subgraph."""
    graph = StateGraph(OneshotState)

    graph.add_node("architect", create_architect_node(config))
    graph.add_node("splitter", create_splitter_node(config))
    graph.add_node("extract_components", _extract_components)

    graph.set_entry_point("architect")
    graph.add_edge("architect", "splitter")
    graph.add_edge("splitter", "extract_components")
    graph.add_edge("extract_components", END)

    return graph
