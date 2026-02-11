"""Architect agent for Stage 3."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage3 import ARCHITECT


def create_architect_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="architect",
        system_prompt="You are a software architect creating high-level designs.",
        user_prompt_template=ARCHITECT,
        output_key="hld",
    )
