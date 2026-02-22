"""Code regenerator agent for Stage 5 — rewrites degenerate files from scratch."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage5 import CODE_REGENERATOR


def create_code_regenerator_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="code_regenerator",
        system_prompt="You are a senior engineer who regenerates broken source files from scratch.",
        user_prompt_template=CODE_REGENERATOR,
        output_key="_regen_result",
    )
