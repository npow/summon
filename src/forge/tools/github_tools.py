"""GitHub integration tools (repo creation, CI setup, releases)."""

from __future__ import annotations

import os
import subprocess

from langchain_core.tools import tool


@tool
def create_github_repo(name: str, description: str, private: bool = False) -> str:
    """Create a new GitHub repository using the gh CLI."""
    visibility = "--private" if private else "--public"
    result = subprocess.run(
        ["gh", "repo", "create", name, visibility, "--description", description],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        return f"Created repo: {result.stdout.strip()}"
    return f"Error: {result.stderr.strip()}"


@tool
def push_to_github(workspace_path: str, repo_url: str) -> str:
    """Initialize git and push workspace to GitHub."""
    commands = [
        "git init",
        "git add -A",
        'git commit -m "Initial commit from Forge"',
        f"git remote add origin {repo_url}",
        "git branch -M main",
        "git push -u origin main",
    ]
    outputs = []
    for cmd in commands:
        result = subprocess.run(
            cmd, shell=True, cwd=workspace_path,
            capture_output=True, text=True, timeout=30,
        )
        outputs.append(f"$ {cmd}\n{result.stdout}{result.stderr}")
        if result.returncode != 0:
            return "\n".join(outputs) + "\nFailed at above command."
    return "\n".join(outputs)


@tool
def create_github_release(repo: str, tag: str, title: str, notes: str) -> str:
    """Create a GitHub release."""
    result = subprocess.run(
        ["gh", "release", "create", tag, "--repo", repo,
         "--title", title, "--notes", notes],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        return f"Release created: {result.stdout.strip()}"
    return f"Error: {result.stderr.strip()}"
