"""Spec writer agent for Stage 1."""

from __future__ import annotations

from summon.agents.base import create_agent_node
from summon.config import SummonConfig
from summon.prompts.stage1 import SELF_CLARIFY, SPEC_WRITER


def create_clarify_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="spec_writer",
        system_prompt="You resolve ambiguities by making practical decisions.",
        user_prompt_template=SELF_CLARIFY,
        output_key="clarifications",
    )


def create_spec_writer_node(config: SummonConfig):
    return create_agent_node(
        config=config,
        model_key="spec_writer",
        system_prompt="You write precise, machine-readable software specifications.",
        user_prompt_template=SPEC_WRITER,
        output_key="spec",
    )
