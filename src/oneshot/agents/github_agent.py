"""GitHub setup agent for Stage 6."""

from __future__ import annotations

from oneshot.agents.base import create_agent_node
from oneshot.config import OneshotConfig
from oneshot.prompts.stage6 import GITHUB_AGENT


def create_github_agent_node(config: OneshotConfig):
    return create_agent_node(
        config=config,
        model_key="github_agent",
        system_prompt="You generate GitHub repository configuration files.",
        user_prompt_template=GITHUB_AGENT,
        output_key="_github_result",
    )
