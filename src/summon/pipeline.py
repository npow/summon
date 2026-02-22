"""Top-level StateGraph connecting all 6 stages with supervisor gates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END, START

from summon.config import SummonConfig
from summon.state import SummonState
from summon.supervisor import create_gate_node, gate_passed
from summon.stages.stage1_idea import create_stage1_graph
from summon.stages.stage2_planning import create_stage2_graph
from summon.stages.stage3_design import create_stage3_graph
from summon.stages.stage4_implement import create_stage4_graph
from summon.stages.stage5_testing import create_stage5_graph
from summon.stages.stage6_release import create_stage6_graph
from summon.workspace import Workspace

logger = logging.getLogger(__name__)

# Default location for checkpoint databases.
_CHECKPOINT_DIR = Path.home() / ".summon" / "checkpoints"


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


def get_checkpointer(run_id: str | None = None):
    """Create a persistent checkpointer for pipeline state.

    Tries to use SqliteSaver (requires ``langgraph-checkpoint-sqlite``).
    Falls back to MemorySaver (in-process only, no cross-run resume).
    Returns ``None`` when no checkpointing is requested (*run_id* is None).
    """
    if run_id is None:
        return None

    try:
        import sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver

        _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        db_path = _CHECKPOINT_DIR / f"{run_id}.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        return SqliteSaver(conn)
    except ImportError:
        logger.info(
            "langgraph-checkpoint-sqlite not installed — "
            "using in-memory checkpointer (no cross-run resume). "
            "Install with: pip install 'summon[checkpoint]'"
        )
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()


def build_pipeline(
    config: SummonConfig | None = None,
    skip_gates: bool = False,
    skip_github: bool = False,
    skip_publish: bool = False,
    until_stage: int = 6,
    from_stage: int = 1,
    checkpointer: Any = None,
) -> Any:
    """Build the Summon pipeline graph.

    Args:
        config: Summon configuration (uses defaults if None)
        skip_gates: If True, skip supervisor gates (for testing)
        skip_github: If True, skip GitHub integration in Stage 6
        skip_publish: If True, skip publishing in Stage 6
        until_stage: Stop after this stage (1-6, inclusive)
        from_stage: Start from this stage (1-6, inclusive)
        checkpointer: Optional LangGraph checkpointer for resume support
    """
    if config is None:
        config = SummonConfig()

    if not (1 <= from_stage <= 6):
        raise ValueError(f"from_stage must be 1-6, got {from_stage}")
    if not (1 <= until_stage <= 6):
        raise ValueError(f"until_stage must be 1-6, got {until_stage}")
    if from_stage > until_stage:
        raise ValueError(f"from_stage ({from_stage}) must be <= until_stage ({until_stage})")

    graph = StateGraph(SummonState)

    # Filter to only the stages in the requested range
    active_stages = [s for s in _STAGES if from_stage <= s[0] <= until_stage]

    # Compile stage subgraphs and add nodes
    compiled = {}
    for num, prefix, stage_key, create_func, gate_artifact in active_stages:
        if prefix == "stage6":
            compiled[prefix] = create_func(
                config, skip_github=skip_github, skip_publish=skip_publish,
            ).compile()
        else:
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

    compile_kwargs: dict[str, Any] = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer

    return graph.compile(**compile_kwargs)
