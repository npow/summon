"""Temporary workspace manager for generated code."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class Workspace:
    """Manages a temporary directory for generated project files."""

    def __init__(self, base_dir: str | Path | None = None):
        if base_dir:
            self.path = Path(base_dir)
            self.path.mkdir(parents=True, exist_ok=True)
            self._temp_dir = None
        else:
            self._temp_dir = tempfile.mkdtemp(prefix="forge_")
            self.path = Path(self._temp_dir)

    def write_file(self, relative_path: str, content: str) -> Path:
        """Write a file into the workspace."""
        full_path = self.path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return full_path

    def read_file(self, relative_path: str) -> str:
        """Read a file from the workspace."""
        return (self.path / relative_path).read_text()

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists in the workspace."""
        return (self.path / relative_path).exists()

    def list_files(self, pattern: str = "**/*") -> list[str]:
        """List files matching a glob pattern."""
        return [
            str(p.relative_to(self.path))
            for p in self.path.glob(pattern)
            if p.is_file()
        ]

    def cleanup(self) -> None:
        """Remove the workspace directory."""
        if self._temp_dir and Path(self._temp_dir).exists():
            shutil.rmtree(self._temp_dir)

    def __str__(self) -> str:
        return str(self.path)


def normalize_file_entry(entry: dict) -> tuple[str, str]:
    """Extract (path, content) from an LLM-produced file dict.

    LLMs may use varying key names like "filepath", "filename", "file_path"
    instead of "path", or "code", "source", "body" instead of "content".
    Returns ("", "") if neither can be resolved.
    """
    path = (
        entry.get("path")
        or entry.get("filepath")
        or entry.get("file_path")
        or entry.get("filename")
        or entry.get("file_name")
        or ""
    )
    content = (
        entry.get("content")
        or entry.get("code")
        or entry.get("source")
        or entry.get("body")
        or ""
    )
    return str(path).strip(), str(content)
