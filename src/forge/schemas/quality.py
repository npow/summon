"""Pydantic schema for supervisor gate evaluation results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GateResult(BaseModel):
    """Supervisor gate evaluation result."""
    stage: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    conformance: float = Field(ge=0.0, le=1.0, description="How well output matches spec")
    quality: float = Field(ge=0.0, le=1.0, description="Overall quality of output")
    coherence: float = Field(ge=0.0, le=1.0, description="Internal consistency")
    scope_creep: float = Field(ge=0.0, le=1.0, description="0=no creep, 1=severe creep")
    feedback: str = Field(description="Detailed feedback for the stage if it fails")
    corrections: list[str] = Field(default_factory=list, description="Specific corrections needed")
