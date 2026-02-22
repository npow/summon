"""Documentation writer agent for Stage 6."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage6 import DOCS_WRITER


def create_docs_writer_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="docs_writer",
        system_prompt="You write clear, comprehensive documentation for software projects.",
        user_prompt_template=DOCS_WRITER,
        output_key="_docs_result",
    )
