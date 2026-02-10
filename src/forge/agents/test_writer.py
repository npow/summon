"""Test writer agent for Stage 5."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage5 import TEST_WRITER


def create_test_writer_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="test_writer",
        system_prompt="You write comprehensive tests for software projects.",
        user_prompt_template=TEST_WRITER,
        output_key="_test_result",
    )
