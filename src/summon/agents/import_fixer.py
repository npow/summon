"""Import fixer agent for Stage 5 — fixes Python import errors."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage5 import IMPORT_FIXER


def create_import_fixer_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="import_fixer",
        system_prompt="You are a Python import debugging expert who fixes import errors.",
        user_prompt_template=IMPORT_FIXER,
        output_key="_import_fix_result",
    )
