"""Pydantic schema for release/packaging info."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReleaseInfo(BaseModel):
    """Release information produced in Stage 6."""
    project_name: str
    version: str = "0.1.0"
    package_files: list[str] = Field(default_factory=list, description="Paths to packaging files created")
    readme_path: str = ""
    github_repo_url: str = ""
    published_url: str = ""
    changelog: str = ""
