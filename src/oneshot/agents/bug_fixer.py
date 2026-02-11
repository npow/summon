"""Bug fixer agent for Stage 5."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage5 import BUG_FIXER


def create_bug_fixer_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="bug_fixer",
        system_prompt="You are a debugging expert who fixes failing tests.",
        user_prompt_template=BUG_FIXER,
        output_key="_fix_result",
    )
