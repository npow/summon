"""Stage 3: High-Level Design — Architect → Component splitter."""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from summon.agents.architect import create_architect_node
from summon.agents.splitter import create_splitter_node
from summon.config import SummonConfig
from summon.state import SummonState


def _extract_components(state: dict[str, Any]) -> dict[str, Any]:
    """Extract component list from splitter result and HLD."""
    split_result = state.get("_split_result", {})
    hld = state.get("hld", {})

    # Prefer splitter's validated components, fall back to HLD's
    components = split_result.get("components", hld.get("components", []))
    return {"components": components}


def create_stage3_graph(config: SummonConfig) -> StateGraph:
    """Build the Stage 3 subgraph."""
    graph = StateGraph(SummonState)

    graph.add_node("architect", create_architect_node(config))
    graph.add_node("splitter", create_splitter_node(config))
    graph.add_node("extract_components", _extract_components)

    graph.set_entry_point("architect")
    graph.add_edge("architect", "splitter")
    graph.add_edge("splitter", "extract_components")
    graph.add_edge("extract_components", END)

    return graph
