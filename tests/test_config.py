"""Tests for oneshot configuration."""

import tempfile
from pathlib import Path

from oneshot.config import OneshotConfig


def test_default_config():
    config = OneshotConfig()
    assert config.max_stage_retries == 3
    assert config.quality_thresholds.idea_refinement == 0.7
    assert "supervisor" in config.models


def test_get_model():
    config = OneshotConfig()
    assert config.get_model("supervisor").startswith("claude")
    assert config.get_model("coder").startswith("claude")
    # Unknown role falls back to supervisor model
    assert config.get_model("nonexistent").startswith("claude")


def test_get_threshold():
    config = OneshotConfig()
    assert config.get_threshold("idea_refinement") == 0.7
    assert config.get_threshold("implementation") == 0.8
    # Unknown stage falls back to default
    assert config.get_threshold("nonexistent") == 0.7


def test_load_from_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("max_stage_retries: 5\n")
        f.write("models:\n  supervisor: gpt-4o\n")
        f.flush()
        config = OneshotConfig.load(f.name)

    assert config.max_stage_retries == 5
    assert config.get_model("supervisor") == "gpt-4o"


def test_load_missing_file():
    config = OneshotConfig.load("/nonexistent/path/oneshot.yaml")
    assert config.max_stage_retries == 3  # defaults
