"""Low-Level Design agent for Stage 4."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage4 import LLD_WRITER


def create_lld_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="lld",
        system_prompt="You write detailed low-level implementation designs.",
        user_prompt_template=LLD_WRITER,
        output_key="_lld_result",
    )
