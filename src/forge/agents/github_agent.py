"""GitHub setup agent for Stage 6."""

from __future__ import annotations

from forge.agents.base import create_agent_node
from forge.config import ForgeConfig
from forge.prompts.stage6 import GITHUB_AGENT


def create_github_agent_node(config: ForgeConfig):
    return create_agent_node(
        config=config,
        model_key="github_agent",
        system_prompt="You generate GitHub repository configuration files.",
        user_prompt_template=GITHUB_AGENT,
        output_key="_github_result",
    )
