"""Integrator agent for Stage 5."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage5 import INTEGRATOR


def create_integrator_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="integrator",
        system_prompt="You integrate independently-built components into a cohesive project.",
        user_prompt_template=INTEGRATOR,
        output_key="_integration_result",
    )
