"""Code reviewer agent for Stage 4."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage4 import CODE_REVIEWER


def create_code_reviewer_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="code_reviewer",
        system_prompt="You are a senior code reviewer focused on correctness and quality.",
        user_prompt_template=CODE_REVIEWER,
        output_key="_review_result",
    )
