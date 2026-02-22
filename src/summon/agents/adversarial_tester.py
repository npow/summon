"""Adversarial test writer agent for Stage 5 — generates edge-case tests from source code."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage5 import ADVERSARIAL_TEST_WRITER


def create_adversarial_tester_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="adversarial_tester",
        system_prompt="You are an adversarial test engineer who finds edge-case bugs by analyzing source code.",
        user_prompt_template=ADVERSARIAL_TEST_WRITER,
        output_key="_adversarial_test_result",
    )
