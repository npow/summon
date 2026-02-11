"""Acceptance criteria generator agent for Stage 5."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage5 import ACCEPTANCE_CRITERIA_GENERATOR


def create_acceptance_criteria_gen_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="acceptance_criteria_gen",
        system_prompt="You are a QA engineer who writes concrete acceptance criteria.",
        user_prompt_template=ACCEPTANCE_CRITERIA_GENERATOR,
        output_key="_acceptance_gen_result",
    )
