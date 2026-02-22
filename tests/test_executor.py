"""Tests for subprocess executor."""

import tempfile
from pathlib import Path

from summon.executor import run_command


def test_successful_command():
    with tempfile.TemporaryDirectory() as d:
        result = run_command("echo hello", cwd=d)
        assert result.success
        assert "hello" in result.stdout


def test_failed_command():
    with tempfile.TemporaryDirectory() as d:
        result = run_command("false", cwd=d)
        assert not result.success
        assert result.returncode != 0


def test_timeout():
    with tempfile.TemporaryDirectory() as d:
        result = run_command("sleep 10", cwd=d, timeout=1)
        assert not result.success
        assert "timed out" in result.stderr.lower()


def test_output_property():
    with tempfile.TemporaryDirectory() as d:
        result = run_command("echo stdout_text && echo stderr_text >&2", cwd=d)
        assert "stdout_text" in result.output
        assert "stderr_text" in result.output


def test_list_command():
    with tempfile.TemporaryDirectory() as d:
        result = run_command(["echo", "hello"], cwd=d)
        assert result.success
        assert "hello" in result.stdout
