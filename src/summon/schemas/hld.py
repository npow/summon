"""Pydantic schema for High-Level Design and component breakdown."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComponentDesign(BaseModel):
    """A single component identified for parallel implementation."""
    id: str = Field(description="Component ID, e.g. comp-001")
    name: str
    description: str
    files: list[str] = Field(description="File paths this component will produce")
    dependencies: list[str] = Field(default_factory=list, description="Other component IDs this depends on")
    interfaces: list[str] = Field(default_factory=list, description="Public interfaces/exports")


class HLD(BaseModel):
    """High-Level Design produced in Stage 3."""
    project_name: str
    module_diagram: str = Field(description="Text-based module relationship diagram")
    components: list[ComponentDesign]
    shared_types: list[str] = Field(default_factory=list, description="Shared type definitions")
    entry_point: str = Field(description="Main entry point file path")
