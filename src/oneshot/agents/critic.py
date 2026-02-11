"""Critic agent for Stage 2."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage2 import CRITIC


def create_critic_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="critic",
        system_prompt="You are a strict technical critic reviewing planning documents.",
        user_prompt_template=CRITIC,
        output_key="_critic_result",
    )
