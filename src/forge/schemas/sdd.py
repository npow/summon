"""Pydantic schema for System Design Document."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TechChoice(BaseModel):
    category: str = Field(description="e.g. framework, database, testing")
    choice: str
    rationale: str


class APIEndpoint(BaseModel):
    method: str
    path: str
    description: str
    request_schema: str = ""
    response_schema: str = ""


class SDD(BaseModel):
    """System Design Document produced in Stage 2."""
    architecture_style: str = Field(description="e.g. monolith, microservices, serverless")
    tech_stack: list[TechChoice]
    api_endpoints: list[APIEndpoint] = Field(default_factory=list)
    data_models: list[str] = Field(default_factory=list, description="Key data model descriptions")
    directory_structure: str = Field(description="Proposed project directory tree")
    dependencies: list[str] = Field(description="Third-party packages needed")
