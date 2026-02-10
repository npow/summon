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
