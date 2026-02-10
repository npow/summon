"""Coder agent for Stage 4."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage4 import CODER


def create_coder_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="coder",
        system_prompt="You are an expert programmer who writes production-quality code.",
        user_prompt_template=CODER,
        output_key="_code_result",
    )
