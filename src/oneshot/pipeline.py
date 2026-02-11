"""Top-level StateGraph connecting all 6 stages with supervisor gates."""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph, END, START

from oneshot.config import OneshotConfig
from oneshot.state import OneshotState
from oneshot.supervisor import create_gate_node, gate_passed
from oneshot.stages.stage1_idea import create_stage1_graph
from oneshot.stages.stage2_planning import create_stage2_graph
from oneshot.stages.stage3_design import create_stage3_graph
from oneshot.stages.stage4_implement import create_stage4_graph
from oneshot.stages.stage5_testing import create_stage5_graph
from oneshot.stages.stage6_release import create_stage6_graph
from oneshot.workspace import Workspace


# Stage definitions: (number, node_prefix, stage_key, create_func, gate_artifact)
_STAGES = [
    (1, "stage1", "idea_refinement", create_stage1_graph, "spec"),
    (2, "stage2", "product_planning", create_stage2_graph, "sdd"),
    (3, "stage3", "design", create_stage3_graph, "hld"),
    (4, "stage4", "implementation", create_stage4_graph, "component_results"),
    (5, "stage5", "integration_testing", create_stage5_graph, "test_results"),
    (6, "stage6", "release", create_stage6_graph, "release_info"),
]


def _init_state(state: dict[str, Any]) -> dict[str, Any]:
    """Initialize pipeline state. Preserves workspace_path if already set."""
    existing_ws = state.get("workspace_path")
    if existing_ws:
        ws = Workspace(existing_ws)
    else:
        ws = Workspace()
    return {
        "workspace_path": str(ws.path),
        "gate_results": [],
        "stage_retries": {},
        "component_results": [],
        "current_stage": "init",
    }


def _set_stage(stage_name: str):
    """Return a node that sets the current stage."""
    def node(state: dict[str, Any]) -> dict[str, Any]:
        return {"current_stage": stage_name}
    return node


def build_pipeline(
    config: OneshotConfig | None = None,
    skip_gates: bool = False,
    skip_github: bool = False,
    skip_publish: bool = False,
    until_stage: int = 6,
    from_stage: int = 1,
) -> Any:
    """Build the Oneshot pipeline graph.

    Args:
        config: Oneshot configuration (uses defaults if None)
        skip_gates: If True, skip supervisor gates (for testing)
        skip_github: If True, skip GitHub integration in Stage 6
        skip_publish: If True, skip publishing in Stage 6
        until_stage: Stop after this stage (1-6, inclusive)
        from_stage: Start from this stage (1-6, inclusive)
    """
    if config is None:
        config = OneshotConfig()

    if not (1 <= from_stage <= 6):
        raise ValueError(f"from_stage must be 1-6, got {from_stage}")
    if not (1 <= until_stage <= 6):
        raise ValueError(f"until_stage must be 1-6, got {until_stage}")
    if from_stage > until_stage:
        raise ValueError(f"from_stage ({from_stage}) must be <= until_stage ({until_stage})")

    graph = StateGraph(OneshotState)

    # Filter to only the stages in the requested range
    active_stages = [s for s in _STAGES if from_stage <= s[0] <= until_stage]

    # Compile stage subgraphs and add nodes
    compiled = {}
    for num, prefix, stage_key, create_func, gate_artifact in active_stages:
        compiled[prefix] = create_func(config).compile()
        mark_name = f"{prefix}_mark"
        graph.add_node(mark_name, _set_stage(stage_key))
        graph.add_node(prefix, compiled[prefix])

        if not skip_gates:
            gate_name = f"gate{num}"
            graph.add_node(gate_name, create_gate_node(config, stage_key, gate_artifact))

    # Always need init
    graph.add_node("init", _init_state)
    graph.set_entry_point("init")

    # Wire init to first active stage
    first_prefix = active_stages[0][1]
    graph.add_edge("init", f"{first_prefix}_mark")

    # Wire each stage to the next (or to END)
    for i, (num, prefix, stage_key, _, _) in enumerate(active_stages):
        mark_name = f"{prefix}_mark"
        gate_name = f"gate{num}"

        # mark → stage
        graph.add_edge(mark_name, prefix)

        is_last = (i == len(active_stages) - 1)

        if is_last:
            # Last active stage → END
            if skip_gates:
                graph.add_edge(prefix, END)
            else:
                graph.add_edge(prefix, gate_name)
                graph.add_conditional_edges(gate_name, gate_passed, {
                    "pass": END,
                    "retry": mark_name,
                })
        else:
            # Wire to next stage
            next_prefix = active_stages[i + 1][1]
            next_mark = f"{next_prefix}_mark"

            if skip_gates:
                graph.add_edge(prefix, next_mark)
            else:
                graph.add_edge(prefix, gate_name)
                graph.add_conditional_edges(gate_name, gate_passed, {
                    "pass": next_mark,
                    "retry": mark_name,
                })

    return graph.compile()
