"""Acceptance test script generator agent for Stage 5."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage5 import ACCEPTANCE_TEST_GENERATOR


def create_acceptance_test_gen_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="acceptance_test_gen",
        system_prompt="You are a QA automation engineer who writes end-to-end test scripts.",
        user_prompt_template=ACCEPTANCE_TEST_GENERATOR,
        output_key="_acceptance_test_gen_result",
    )
