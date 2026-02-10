"""Packager agent for Stage 6."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage6 import PACKAGER


def create_packager_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="packager",
        system_prompt="You create distribution-ready package configurations.",
        user_prompt_template=PACKAGER,
        output_key="_package_result",
    )
