"""Integrator agent for Stage 5."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage5 import INTEGRATOR


def create_integrator_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="integrator",
        system_prompt="You integrate independently-built components into a cohesive project.",
        user_prompt_template=INTEGRATOR,
        output_key="_integration_result",
    )
