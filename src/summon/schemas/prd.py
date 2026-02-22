"""Pydantic schema for Product Requirements Document."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UserStory(BaseModel):
    id: str
    persona: str
    action: str
    benefit: str
    acceptance_criteria: list[str]


class PRD(BaseModel):
    """Product Requirements Document produced in Stage 2."""
    project_name: str
    vision: str
    user_stories: list[UserStory]
    mvp_scope: list[str] = Field(description="Feature IDs included in MVP")
    success_metrics: list[str]
