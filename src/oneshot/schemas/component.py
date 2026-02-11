"""Pydantic schema for component implementation results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FileOutput(BaseModel):
    path: str
    content: str


class CodeReviewFeedback(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ComponentResult(BaseModel):
    """Result from implementing a single component in Stage 4."""
    component_id: str
    files: list[FileOutput]
    review_feedback: CodeReviewFeedback | None = None
    lld_summary: str = ""
