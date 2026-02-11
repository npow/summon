"""Package registry publishing tools."""

from __future__ import annotations

import subprocess

from langchain_core.tools import tool


@tool
def publish_pypi(workspace_path: str, test_pypi: bool = True) -> str:
    """Build and publish a Python package to PyPI (or TestPyPI)."""
    # Build
    build_result = subprocess.run(
        ["python", "-m", "build"],
        cwd=workspace_path, capture_output=True, text=True, timeout=60,
    )
    if build_result.returncode != 0:
        return f"Build failed: {build_result.stderr}"

    # Upload
    repo_flag = ["--repository", "testpypi"] if test_pypi else []
    upload_result = subprocess.run(
        ["python", "-m", "twine", "upload", *repo_flag, "dist/*"],
        cwd=workspace_path, capture_output=True, text=True, timeout=60,
    )
    if upload_result.returncode != 0:
        return f"Upload failed: {upload_result.stderr}"
    return f"Published successfully: {upload_result.stdout}"


@tool
def publish_npm(workspace_path: str) -> str:
    """Publish a Node.js package to npm."""
    result = subprocess.run(
        ["npm", "publish"],
        cwd=workspace_path, capture_output=True, text=True, timeout=60,
    )
    if result.returncode == 0:
        return f"Published: {result.stdout}"
    return f"Error: {result.stderr}"
