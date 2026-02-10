"""Stage 2: Product Planning — PRD → SDD → Critic (loop until pass)."""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END

from forge.agents.prd import create_prd_node
from forge.agents.sdd import create_sdd_node
from forge.agents.critic import create_critic_node
from forge.config import ForgeConfig
from forge.state import ForgeState


def _process_critic(state: dict[str, Any]) -> dict[str, Any]:
    """Process critic output and set planning_approved flag."""
    result = state.get("_critic_result", {})
    approved = result.get("approved", False)
    feedback = ""
    if not approved:
        issues = result.get("issues", [])
        suggestions = result.get("suggestions", [])
        feedback = "Issues:\n" + "\n".join(f"- {i}" for i in issues)
        if suggestions:
            feedback += "\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
    return {
        "planning_approved": approved,
        "critic_feedback": feedback,
    }


def _critic_decision(state: dict[str, Any]) -> str:
    """Route based on critic approval."""
    if state.get("planning_approved", False):
        return "approved"
    # Check retry count
    retries = state.get("stage_retries", {}).get("planning_critic", 0)
    if retries >= 3:
        return "approved"  # Force pass after max retries
    return "revise"


def _increment_critic_retries(state: dict[str, Any]) -> dict[str, Any]:
    """Track critic loop retries."""
    retries = dict(state.get("stage_retries", {}))
    retries["planning_critic"] = retries.get("planning_critic", 0) + 1
    return {"stage_retries": retries}


def create_stage2_graph(config: ForgeConfig) -> StateGraph:
    """Build the Stage 2 subgraph with critic loop."""
    graph = StateGraph(ForgeState)

    graph.add_node("write_prd", create_prd_node(config))
    graph.add_node("write_sdd", create_sdd_node(config))
    graph.add_node("critic", create_critic_node(config))
    graph.add_node("process_critic", _process_critic)
    graph.add_node("increment_retries", _increment_critic_retries)

    graph.set_entry_point("write_prd")
    graph.add_edge("write_prd", "write_sdd")
    graph.add_edge("write_sdd", "critic")
    graph.add_edge("critic", "process_critic")
    graph.add_conditional_edges(
        "process_critic",
        _critic_decision,
        {
            "approved": END,
            "revise": "increment_retries",
        }
    )
    graph.add_edge("increment_retries", "write_prd")

    return graph
