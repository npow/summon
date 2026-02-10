"""Pydantic schema for the idea spec — the immutable contract for the pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FunctionalRequirement(BaseModel):
    id: str = Field(description="Unique requirement ID, e.g. FR-001")
    description: str
    priority: str = Field(description="high, medium, or low")


class NonFunctionalRequirement(BaseModel):
    id: str = Field(description="Unique requirement ID, e.g. NFR-001")
    category: str = Field(description="e.g. performance, security, usability")
    description: str


class IdeaSpec(BaseModel):
    """The spec produced by Stage 1. Immutable contract for all downstream stages."""
    project_name: str = Field(description="Short, kebab-case project name")
    one_liner: str = Field(description="One-sentence description of what the product does")
    target_users: list[str] = Field(description="Who will use this product")
    language: str = Field(description="Primary programming language (python, typescript, go)")
    package_type: str = Field(description="cli, library, web-app, api-server")
    functional_requirements: list[FunctionalRequirement]
    non_functional_requirements: list[NonFunctionalRequirement] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list, description="Technical or business constraints")
    out_of_scope: list[str] = Field(default_factory=list, description="Explicitly excluded features")
