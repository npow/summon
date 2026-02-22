"""Publisher agent for Stage 6."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage6 import PUBLISHER


def create_publisher_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="publisher",
        system_prompt="You determine how to publish packages to registries.",
        user_prompt_template=PUBLISHER,
        output_key="_publish_result",
    )
