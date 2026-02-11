"""Sandboxed shell execution tools."""

from __future__ import annotations

from langchain_core.tools import tool

from oneshot.executor import run_command


def create_shell_tools(workspace_path: str):
    """Create shell tools bound to a specific workspace."""

    @tool
    def run_shell(command: str, timeout: int = 60) -> str:
        """Run a shell command in the workspace directory."""
        result = run_command(command, cwd=workspace_path, timeout=timeout)
        output = f"Exit code: {result.returncode}\n{result.output}"
        return output[:5000]  # Truncate for LLM context

    @tool
    def run_tests(test_command: str = "pytest") -> str:
        """Run tests in the workspace."""
        result = run_command(test_command, cwd=workspace_path, timeout=120)
        output = f"Exit code: {result.returncode}\n{result.output}"
        return output[:5000]

    return [run_shell, run_tests]
