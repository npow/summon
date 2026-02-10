"""Subprocess runner for tests and builds in the workspace."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        parts = []
        if self.stdout.strip():
            parts.append(self.stdout.strip())
        if self.stderr.strip():
            parts.append(f"STDERR:\n{self.stderr.strip()}")
        return "\n".join(parts) or "(no output)"


def run_command(
    cmd: str | list[str],
    cwd: str | Path,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> ExecResult:
    """Run a shell command in the given directory."""
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False

    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
            env=env,
        )
        return ExecResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
        )
    except Exception as e:
        return ExecResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
        )
