"""GitHub setup agent for Stage 6."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage6 import GITHUB_AGENT


def create_github_agent_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="github_agent",
        system_prompt="You generate GitHub repository configuration files.",
        user_prompt_template=GITHUB_AGENT,
        output_key="_github_result",
    )
