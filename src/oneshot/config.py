"""Pydantic configuration loaded from oneshot.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class QualityThresholds(BaseModel):
    idea_refinement: float = 0.7
    product_planning: float = 0.75
    design: float = 0.75
    implementation: float = 0.8
    integration_testing: float = 0.85
    release: float = 0.8


class OneshotConfig(BaseModel):
    models: dict[str, str] = Field(default_factory=lambda: {
        "supervisor": "claude-sonnet-4-20250514",
        "ambiguity": "claude-sonnet-4-20250514",
        "spec_writer": "claude-sonnet-4-20250514",
        "prd": "claude-sonnet-4-20250514",
        "sdd": "claude-sonnet-4-20250514",
        "critic": "claude-sonnet-4-20250514",
        "architect": "claude-sonnet-4-20250514",
        "splitter": "claude-sonnet-4-20250514",
        "lld": "claude-sonnet-4-20250514",
        "coder": "claude-sonnet-4-20250514",
        "code_reviewer": "claude-sonnet-4-20250514",
        "integrator": "claude-sonnet-4-20250514",
        "test_writer": "gpt-4o-mini",
        "bug_fixer": "claude-sonnet-4-20250514",
        "import_fixer": "claude-sonnet-4-20250514",
        "code_regenerator": "claude-sonnet-4-20250514",
        "acceptance_criteria_gen": "claude-sonnet-4-20250514",
        "acceptance_test_gen": "claude-sonnet-4-20250514",
        "acceptance_fixer": "claude-sonnet-4-20250514",
        "packager": "gpt-4o-mini",
        "docs_writer": "gpt-4o-mini",
        "github_agent": "gpt-4o-mini",
        "publisher": "gpt-4o-mini",
    })
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)
    max_stage_retries: int = 3

    @classmethod
    def load(cls, path: str | Path | None = None) -> OneshotConfig:
        """Load config from YAML file, falling back to defaults."""
        if path is None:
            path = Path.cwd() / "oneshot.yaml"
        path = Path(path)
        if path.exists():
            with open(path) as f:
                data: dict[str, Any] = yaml.safe_load(f) or {}
            return cls.model_validate(data)
        return cls()

    def get_model(self, role: str) -> str:
        """Get model name for a given agent role."""
        return self.models.get(role, self.models.get("supervisor", "claude-sonnet-4-20250514"))

    def get_threshold(self, stage: str) -> float:
        """Get quality threshold for a given stage name."""
        return getattr(self.quality_thresholds, stage, 0.7)
