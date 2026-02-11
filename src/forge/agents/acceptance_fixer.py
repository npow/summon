"""Acceptance test fixer agent for Stage 5 — fixes source code to pass acceptance tests."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage5 import ACCEPTANCE_BUG_FIXER


def create_acceptance_fixer_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="acceptance_fixer",
        system_prompt="You are a debugging expert who fixes code to pass acceptance tests.",
        user_prompt_template=ACCEPTANCE_BUG_FIXER,
        output_key="_acceptance_fix_result",
    )
