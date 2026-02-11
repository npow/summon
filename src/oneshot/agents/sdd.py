"""SDD writer agent for Stage 2."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage2 import SDD_WRITER


def create_sdd_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="sdd",
        system_prompt="You are a software architect creating system design documents.",
        user_prompt_template=SDD_WRITER,
        output_key="sdd",
    )
