"""File operation tools for the workspace."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool


def create_file_tools(workspace_path: str):
    """Create file tools bound to a specific workspace."""

    @tool
    def write_file(relative_path: str, content: str) -> str:
        """Write content to a file in the workspace."""
        full_path = Path(workspace_path) / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return f"Written {len(content)} bytes to {relative_path}"

    @tool
    def read_file(relative_path: str) -> str:
        """Read a file from the workspace."""
        full_path = Path(workspace_path) / relative_path
        if not full_path.exists():
            return f"Error: {relative_path} not found"
        return full_path.read_text()

    @tool
    def list_files(pattern: str = "**/*") -> str:
        """List files in the workspace matching a glob pattern."""
        ws = Path(workspace_path)
        files = [str(p.relative_to(ws)) for p in ws.glob(pattern) if p.is_file()]
        return "\n".join(files) if files else "No files found"

    return [write_file, read_file, list_files]
