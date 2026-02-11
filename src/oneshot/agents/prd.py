"""PRD writer agent for Stage 2."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage2 import PRD_WRITER


def create_prd_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="prd",
        system_prompt="You are an expert product manager creating PRDs.",
        user_prompt_template=PRD_WRITER,
        output_key="prd",
    )
