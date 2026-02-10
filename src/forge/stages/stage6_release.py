"""Stage 6: Package & Release — Package → Docs → GitHub repo → Publish."""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import StateGraph, END

from forge.agents.packager import create_packager_node
from forge.agents.docs_writer import create_docs_writer_node
from forge.agents.github_agent import create_github_agent_node
from forge.agents.publisher import create_publisher_node
from forge.config import ForgeConfig
from forge.state import ForgeState
from forge.workspace import Workspace


def _build_project_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build file listing for release agents."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"project_files": "(no files)"}

    ws = Workspace(workspace_path)
    files = ws.list_files()
    file_contents = []
    for f in files[:20]:
        try:
            content = ws.read_file(f)
            file_contents.append(f"=== {f} ===\n{content}")
        except Exception:
            pass

    return {"project_files": "\n\n".join(file_contents) or "(no files)"}


def _process_package(state: dict[str, Any]) -> dict[str, Any]:
    """Write packaging files to workspace."""
    result = state.get("_package_result", {})
    files = result.get("files", [])
    workspace_path = state.get("workspace_path", "")

    package_files = []
    if workspace_path and files:
        ws = Workspace(workspace_path)
        for f in files:
            path = f.get("path", "")
            content = f.get("content", "")
            if path and content:
                ws.write_file(path, content)
                package_files.append(path)

    return {"_package_files": package_files}


def _process_docs(state: dict[str, Any]) -> dict[str, Any]:
    """Write documentation files to workspace."""
    result = state.get("_docs_result", {})
    workspace_path = state.get("workspace_path", "")

    if workspace_path:
        ws = Workspace(workspace_path)
        readme = result.get("readme", "")
        if readme:
            ws.write_file("README.md", readme)
        changelog = result.get("changelog", "")
        if changelog:
            ws.write_file("CHANGELOG.md", changelog)

    return {}


def _process_github(state: dict[str, Any]) -> dict[str, Any]:
    """Write GitHub config files to workspace."""
    result = state.get("_github_result", {})
    files = result.get("files", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and files:
        ws = Workspace(workspace_path)
        for f in files:
            path = f.get("path", "")
            content = f.get("content", "")
            if path and content:
                ws.write_file(path, content)

    return {}


def _build_release_info(state: dict[str, Any]) -> dict[str, Any]:
    """Build final release info."""
    spec = state.get("spec", {})
    workspace_path = state.get("workspace_path", "")

    ws = Workspace(workspace_path) if workspace_path else None
    all_files = ws.list_files() if ws else []

    release_info = {
        "project_name": spec.get("project_name", "unknown"),
        "version": "0.1.0",
        "package_files": all_files,
        "readme_path": "README.md",
        "github_repo_url": "",
        "published_url": "",
        "changelog": "## 0.1.0\n- Initial release",
    }

    return {"release_info": release_info}


def create_stage6_graph(config: ForgeConfig) -> StateGraph:
    """Build the Stage 6 subgraph."""
    graph = StateGraph(ForgeState)

    graph.add_node("build_context", _build_project_context)
    graph.add_node("package", create_packager_node(config))
    graph.add_node("process_package", _process_package)
    graph.add_node("write_docs", create_docs_writer_node(config))
    graph.add_node("process_docs", _process_docs)
    graph.add_node("github_setup", create_github_agent_node(config))
    graph.add_node("process_github", _process_github)
    graph.add_node("build_release_info", _build_release_info)

    graph.set_entry_point("build_context")
    graph.add_edge("build_context", "package")
    graph.add_edge("package", "process_package")
    graph.add_edge("process_package", "write_docs")
    graph.add_edge("write_docs", "process_docs")
    graph.add_edge("process_docs", "github_setup")
    graph.add_edge("github_setup", "process_github")
    graph.add_edge("process_github", "build_release_info")
    graph.add_edge("build_release_info", END)

    return graph
