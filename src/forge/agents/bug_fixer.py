"""Bug fixer agent for Stage 5."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage5 import BUG_FIXER


def create_bug_fixer_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="bug_fixer",
        system_prompt="You are a debugging expert who fixes failing tests.",
        user_prompt_template=BUG_FIXER,
        output_key="_fix_result",
    )
