"""Ambiguity detection agent for Stage 1."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage1 import AMBIGUITY_DETECTION


def create_ambiguity_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="ambiguity",
        system_prompt="You are an expert product analyst who identifies ambiguities in software ideas.",
        user_prompt_template=AMBIGUITY_DETECTION,
        output_key="ambiguities",
    )
