"""Component splitter agent for Stage 3."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage3 import COMPONENT_SPLITTER


def create_splitter_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="splitter",
        system_prompt="You validate and refine component breakdowns for parallel implementation.",
        user_prompt_template=COMPONENT_SPLITTER,
        output_key="_split_result",
    )
