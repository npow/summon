"""Coder agent for Stage 4."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage4 import CODER


def create_coder_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="coder",
        system_prompt="You are an expert programmer who writes production-quality code.",
        user_prompt_template=CODER,
        output_key="_code_result",
    )
