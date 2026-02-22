"""Adversarial bug fixer agent for Stage 5 — fixes source code to pass adversarial tests."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage5 import ADVERSARIAL_BUG_FIXER


def create_adversarial_fixer_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="bug_fixer",
        system_prompt="You are a debugging expert who fixes code to handle edge cases found by adversarial testing.",
        user_prompt_template=ADVERSARIAL_BUG_FIXER,
        output_key="_adversarial_fix_result",
    )
