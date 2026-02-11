"""Packager agent for Stage 6."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage6 import PACKAGER


def create_packager_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="packager",
        system_prompt="You create distribution-ready package configurations.",
        user_prompt_template=PACKAGER,
        output_key="_package_result",
    )
