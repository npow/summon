"""Ambiguity detection agent for Stage 1."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage1 import AMBIGUITY_DETECTION


def create_ambiguity_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="ambiguity",
        system_prompt="You are an expert product analyst who identifies ambiguities in software ideas.",
        user_prompt_template=AMBIGUITY_DETECTION,
        output_key="ambiguities",
    )
