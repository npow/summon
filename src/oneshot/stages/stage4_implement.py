"""Stage 4: Implementation — Send fan-out: LLD → Code → Review per component."""

from __future__ import annotations

import json
import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import StateGraph, END, START
from langgraph.types import Send

from oneshot.agents.lld import create_lld_node
from oneshot.agents.coder import create_coder_node
from oneshot.agents.code_reviewer import create_code_reviewer_node
from oneshot.config import OneshotConfig
from oneshot.state import OneshotState


class ComponentOutput(TypedDict, total=False):
    """Output schema — ONLY component_results flows back to parent."""
    component_results: Annotated[list[dict[str, Any]], operator.add]


class ComponentState(TypedDict, total=False):
    """Isolated state for per-component subgraph."""
    # Input context
    spec: dict[str, Any]
    hld: dict[str, Any]
    component: dict[str, Any]
    language: str

    # Internal working state
    _lld_result: dict[str, Any]
    _code_result: dict[str, Any]
    _review_result: dict[str, Any]
    _review_retries: int

    # Output — aggregated by parent
    component_results: Annotated[list[dict[str, Any]], operator.add]


def _prepare_component(state: dict[str, Any]) -> dict[str, Any]:
    """Set up component state for implementation."""
    return {
        "language": state.get("spec", {}).get("language", "python"),
        "_review_retries": 0,
    }


def _review_decision(state: dict[str, Any]) -> str:
    """Route based on review approval."""
    review = state.get("_review_result", {})
    if review.get("approved", True):
        return "approved"
    retries = state.get("_review_retries", 0)
    if retries >= 2:
        return "approved"
    return "revise"


def _increment_review_retries(state: dict[str, Any]) -> dict[str, Any]:
    return {"_review_retries": state.get("_review_retries", 0) + 1}


def _collect_result(state: dict[str, Any]) -> dict[str, Any]:
    """Package component result for aggregation."""
    component = state.get("component", {})
    code_result = state.get("_code_result", {})
    review = state.get("_review_result", {})
    lld = state.get("_lld_result", {})

    result = {
        "component_id": component.get("id", "unknown"),
        "files": code_result.get("files", []),
        "review_feedback": review,
        "lld_summary": lld.get("lld_summary", "") if isinstance(lld, dict) else str(lld),
    }
    return {"component_results": [result]}


def create_component_graph(config: OneshotConfig) -> StateGraph:
    """Build the per-component subgraph: LLD → Code → Review loop.

    Uses ComponentState (not OneshotState) to avoid key conflicts when
    multiple Send branches merge back into the parent graph.
    """
    graph = StateGraph(ComponentState, output_schema=ComponentOutput)

    graph.add_node("prepare", _prepare_component)
    graph.add_node("lld", create_lld_node(config))
    graph.add_node("code", create_coder_node(config))
    graph.add_node("review", create_code_reviewer_node(config))
    graph.add_node("increment_retries", _increment_review_retries)
    graph.add_node("collect", _collect_result)

    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "lld")
    graph.add_edge("lld", "code")
    graph.add_edge("code", "review")
    graph.add_conditional_edges(
        "review",
        _review_decision,
        {
            "approved": "collect",
            "revise": "increment_retries",
        }
    )
    graph.add_edge("increment_retries", "code")
    graph.add_edge("collect", END)

    return graph


def fan_out_components(state: dict[str, Any]) -> list[Send]:
    """Fan out to one subgraph per component using Send API.

    Only sends the keys defined in ComponentState — no extra OneshotState keys.
    """
    components = state.get("components", [])
    spec = state.get("spec", {})
    hld = state.get("hld", {})

    base_context = {
        "spec": spec,
        "hld": hld,
        "component_results": [],
    }

    if not components:
        component = {
            "id": "single", "name": "main",
            "description": "entire project",
            "files": [], "dependencies": [], "interfaces": [],
        }
        return [Send("implement_component", {**base_context, "component": component})]

    return [
        Send("implement_component", {**base_context, "component": comp})
        for comp in components
    ]


def _write_files_to_workspace(state: dict[str, Any]) -> dict[str, Any]:
    """Write all component files to the workspace directory."""
    from oneshot.workspace import Workspace, normalize_file_entry

    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        ws = Workspace()
        workspace_path = str(ws.path)
    else:
        ws = Workspace(workspace_path)

    component_results = state.get("component_results", [])
    for result in component_results:
        files = result.get("files", [])
        for f in files:
            path, content = normalize_file_entry(f)
            if path and content:
                ws.write_file(path, content)

    return {"workspace_path": workspace_path}


def create_stage4_graph(config: OneshotConfig) -> StateGraph:
    """Build the Stage 4 graph with Send-based fan-out."""
    component_subgraph = create_component_graph(config).compile()

    graph = StateGraph(OneshotState)

    graph.add_node("implement_component", component_subgraph)
    graph.add_node("write_files", _write_files_to_workspace)

    graph.add_conditional_edges(
        START,
        fan_out_components,
        ["implement_component"],
    )
    graph.add_edge("implement_component", "write_files")
    graph.add_edge("write_files", END)

    return graph
