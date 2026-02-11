"""Publisher agent for Stage 6."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage6 import PUBLISHER


def create_publisher_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="publisher",
        system_prompt="You determine how to publish packages to registries.",
        user_prompt_template=PUBLISHER,
        output_key="_publish_result",
    )
