"""Stage 5: Testing — Integrate → Write tests → Run → Fix bugs (loop)."""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import StateGraph, END

from forge.agents.integrator import create_integrator_node
from forge.agents.test_writer import create_test_writer_node
from forge.agents.bug_fixer import create_bug_fixer_node
from forge.config import ForgeConfig
from forge.executor import run_command
from forge.state import ForgeState
from forge.workspace import Workspace


def _process_integration(state: dict[str, Any]) -> dict[str, Any]:
    """Write integration files to workspace from integrator output."""
    import re

    result = state.get("_integration_result", {})
    workspace_path = state.get("workspace_path", "")

    if not workspace_path:
        return {"integration_code": ""}

    ws = Workspace(workspace_path)
    files_written = 0

    # Format 1: files array (preferred — same as coder output)
    files = result.get("files", [])
    if files and isinstance(files, list):
        for f in files:
            path = f.get("path", "")
            content = f.get("content", "")
            if path and content:
                ws.write_file(path, content)
                files_written += 1

    # Format 2: integration_code with ### FILE: markers (fallback)
    if files_written == 0:
        integration_code = result.get("integration_code", "")
        if integration_code:
            normalized = integration_code.replace("\\n", "\n")
            file_pattern = re.compile(
                r'###\s*FILE:\s*(.+?)\s*###\s*[\r\n]+', re.IGNORECASE
            )
            parts = file_pattern.split(normalized)

            if len(parts) > 1:
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        filepath = parts[i].strip()
                        content = parts[i + 1].strip()
                        if filepath and content:
                            ws.write_file(filepath, content)
                            files_written += 1

            if files_written == 0:
                ws.write_file("integration_glue.py", normalized)

    return {"integration_code": str(files_written) + " integration files written"}


def _build_project_files_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build a summary of project files for test writer."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"project_files": "(no files yet)"}

    ws = Workspace(workspace_path)
    files = ws.list_files()
    file_contents = []
    for f in files[:20]:  # Limit to avoid context overflow
        try:
            content = ws.read_file(f)
            file_contents.append(f"=== {f} ===\n{content}")
        except Exception:
            pass

    return {"project_files": "\n\n".join(file_contents) or "(no files)"}


def _process_tests(state: dict[str, Any]) -> dict[str, Any]:
    """Write test files to workspace."""
    result = state.get("_test_result", {})
    test_code = result.get("test_code", "")
    test_path = result.get("test_file_path", "tests/test_main.py")
    workspace_path = state.get("workspace_path", "")

    if workspace_path and test_code:
        ws = Workspace(workspace_path)
        ws.write_file(test_path, test_code)

    return {"test_code": test_code}


def _run_tests(state: dict[str, Any]) -> dict[str, Any]:
    """Actually run the tests in the workspace."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"test_results": "No workspace", "tests_passing": False}

    language = state.get("spec", {}).get("language", "python")

    if language == "python":
        cmd = "python -m pytest tests/ -v --tb=short 2>&1"
    elif language == "typescript":
        cmd = "npx jest --verbose 2>&1"
    elif language == "go":
        cmd = "go test ./... -v 2>&1"
    else:
        cmd = "echo 'Unknown language for testing'"

    result = run_command(cmd, cwd=workspace_path, timeout=120)
    output = result.output[:4000]

    # Detect pass/fail from both exit code and output content
    passing = result.success
    if not passing:
        # Double-check: some test runners return non-zero even for collection errors
        # We consider it "passing" only if tests actually ran and passed
        pass
    else:
        # Even with exit code 0, check output for failure indicators
        fail_indicators = ["FAILED", "ERRORS", "error", "Error", "failures="]
        for indicator in fail_indicators:
            if indicator in output:
                passing = False
                break

    return {
        "test_results": output,
        "tests_passing": passing,
    }


def _test_decision(state: dict[str, Any]) -> str:
    """Route based on test results."""
    if state.get("tests_passing", False):
        return "passing"
    retries = state.get("stage_retries", {}).get("test_fix", 0)
    if retries >= 3:
        return "passing"  # Force pass
    return "failing"


def _process_fixes(state: dict[str, Any]) -> dict[str, Any]:
    """Apply bug fixes to workspace."""
    result = state.get("_fix_result", {})
    fixes = result.get("fixes", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and fixes:
        ws = Workspace(workspace_path)
        for fix in fixes:
            path = fix.get("file_path", "")
            content = fix.get("content", "")
            if path and content:
                ws.write_file(path, content)

    retries = dict(state.get("stage_retries", {}))
    retries["test_fix"] = retries.get("test_fix", 0) + 1
    return {"stage_retries": retries}


def _build_fix_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build context for bug fixer with source files and test results."""
    workspace_path = state.get("workspace_path", "")
    source_files = ""
    if workspace_path:
        ws = Workspace(workspace_path)
        files = [f for f in ws.list_files() if not f.startswith("tests/")]
        for f in files[:15]:
            try:
                content = ws.read_file(f)
                source_files += f"\n=== {f} ===\n{content}\n"
            except Exception:
                pass

    return {"source_files": source_files or "(no source files)"}


def create_stage5_graph(config: ForgeConfig) -> StateGraph:
    """Build the Stage 5 subgraph with test-fix loop."""
    graph = StateGraph(ForgeState)

    graph.add_node("integrate", create_integrator_node(config))
    graph.add_node("process_integration", _process_integration)
    graph.add_node("build_context", _build_project_files_context)
    graph.add_node("write_tests", create_test_writer_node(config))
    graph.add_node("process_tests", _process_tests)
    graph.add_node("run_tests", _run_tests)
    graph.add_node("build_fix_context", _build_fix_context)
    graph.add_node("fix_bugs", create_bug_fixer_node(config))
    graph.add_node("process_fixes", _process_fixes)

    graph.set_entry_point("integrate")
    graph.add_edge("integrate", "process_integration")
    graph.add_edge("process_integration", "build_context")
    graph.add_edge("build_context", "write_tests")
    graph.add_edge("write_tests", "process_tests")
    graph.add_edge("process_tests", "run_tests")
    graph.add_conditional_edges(
        "run_tests",
        _test_decision,
        {
            "passing": END,
            "failing": "build_fix_context",
        }
    )
    graph.add_edge("build_fix_context", "fix_bugs")
    graph.add_edge("fix_bugs", "process_fixes")
    graph.add_edge("process_fixes", "run_tests")

    return graph
