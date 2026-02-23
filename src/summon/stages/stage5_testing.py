"""Stage 5: Testing — Integrate → Import validation → Unit tests → Acceptance tests."""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from summon.agents.integrator import create_integrator_node
from summon.agents.test_writer import create_test_writer_node
from summon.agents.bug_fixer import create_bug_fixer_node
from summon.agents.import_fixer import create_import_fixer_node
from summon.agents.code_regenerator import create_code_regenerator_node
from summon.agents.acceptance_criteria_gen import create_acceptance_criteria_gen_node
from summon.agents.acceptance_test_gen import create_acceptance_test_gen_node
from summon.agents.acceptance_fixer import create_acceptance_fixer_node
from summon.agents.adversarial_tester import create_adversarial_tester_node
from summon.agents.adversarial_fixer import create_adversarial_fixer_node
from summon.config import SummonConfig
from summon.executor import run_command
from summon.state import SummonState
from summon.workspace import Workspace, collect_file_contents


# ---------------------------------------------------------------------------
# Existing nodes (integration, deps, unit tests)
# ---------------------------------------------------------------------------


def _build_integration_context(state: dict[str, Any]) -> dict[str, Any]:
    """Strip component_results to only files for the integrator prompt.

    The raw component_results include review_feedback and lld_summary which
    are large and unnecessary for integration. Keeping only the files
    dramatically reduces prompt size.
    """
    component_results = state.get("component_results", [])
    slim = []
    for comp in component_results:
        slim.append({
            "component_id": comp.get("component_id", ""),
            "files": comp.get("files", []),
        })
    return {"component_results": slim}


def _process_integration(state: dict[str, Any]) -> dict[str, Any]:
    """Write integration files to workspace from integrator output."""
    import re
    from summon.workspace import normalize_file_entry

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
            path, content = normalize_file_entry(f)
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


def _install_deps(state: dict[str, Any]) -> dict[str, Any]:
    """Install project dependencies in the workspace before running tests.

    Creates a venv via uv and installs requirements into it.
    """
    import shutil

    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {}

    ws = Workspace(workspace_path)
    language = state.get("spec", {}).get("language", "python")

    if language == "python":
        # Create a venv if one doesn't exist
        venv_dir = str(Path(workspace_path) / ".venv")
        uv = shutil.which("uv")
        if uv and not Path(venv_dir).exists():
            run_command(f"{uv} venv {venv_dir} 2>&1", cwd=workspace_path, timeout=30)

        if ws.file_exists("requirements.txt"):
            if uv:
                venv_python = str(Path(venv_dir) / "bin" / "python")
                run_command(
                    f"{uv} pip install -r requirements.txt -p {venv_python} 2>&1",
                    cwd=workspace_path,
                    timeout=180,
                )
                run_command(
                    f"{uv} pip install pytest -p {venv_python} 2>&1",
                    cwd=workspace_path,
                    timeout=60,
                )
            else:
                run_command(
                    "python -m pip install -r requirements.txt 2>&1",
                    cwd=workspace_path,
                    timeout=180,
                )
                run_command("python -m pip install pytest 2>&1", cwd=workspace_path, timeout=60)
    elif language == "typescript":
        if ws.file_exists("package.json"):
            run_command("npm install 2>&1", cwd=workspace_path, timeout=180)
    elif language == "go":
        if ws.file_exists("go.mod"):
            run_command("go mod tidy 2>&1", cwd=workspace_path, timeout=120)

    return {}


def _build_project_files_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build a summary of project files for test writer."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"project_files": "(no files yet)"}

    ws = Workspace(workspace_path)
    files = [
        f for f in ws.list_files()
        if not f.startswith(".venv/")
        and not f.startswith("__pycache__/")
        and "__pycache__/" not in f
        and not f.endswith(".pyc")
    ]
    return {"project_files": collect_file_contents(ws, files)}


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
    import os

    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"test_results": "No workspace", "tests_passing": False}

    language = state.get("spec", {}).get("language", "python")

    if language == "python":
        # Use venv python if available
        venv_python = os.path.join(workspace_path, ".venv", "bin", "python")
        if os.path.exists(venv_python):
            cmd = f"{venv_python} -m pytest tests/ -v --tb=short 2>&1"
        else:
            cmd = "python -m pytest tests/ -v --tb=short 2>&1"
    elif language == "typescript":
        cmd = "npx jest --verbose 2>&1"
    elif language == "go":
        cmd = "go test ./... -v 2>&1"
    else:
        cmd = "echo 'Unknown language for testing'"

    # Set PYTHONPATH so imports from the project root and src/ resolve
    env = os.environ.copy()
    pypath_parts = [workspace_path]
    src_dir = os.path.join(workspace_path, "src")
    if os.path.isdir(src_dir):
        pypath_parts.append(src_dir)
    env["PYTHONPATH"] = os.pathsep.join(pypath_parts)

    result = run_command(cmd, cwd=workspace_path, timeout=120, env=env)
    output = result.output[:4000]

    # Detect pass/fail primarily from exit code.
    passing = result.success
    if passing:
        import re
        fail_patterns = [
            r'\d+ failed',           # pytest: "1 failed"
            r'^FAILED ',             # pytest: "FAILED tests/..."
            r'^ERRORS$',             # pytest collection errors (standalone line)
            r'failures=\d*[1-9]',    # unittest: "failures=1"
            r'Tests:\s+\d+ failed',  # jest: "Tests:  1 failed"
        ]
        for pattern in fail_patterns:
            if re.search(pattern, output, re.MULTILINE):
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
        return "force_pass"
    return "failing"


def _process_fixes(state: dict[str, Any]) -> dict[str, Any]:
    """Apply bug fixes to workspace."""
    from summon.workspace import normalize_file_entry

    result = state.get("_fix_result", {})
    fixes = result.get("fixes", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and fixes:
        ws = Workspace(workspace_path)
        for fix in fixes:
            path, content = normalize_file_entry(fix)
            if path and content:
                ws.write_file(path, content)

    retries = dict(state.get("stage_retries", {}))
    retries["test_fix"] = retries.get("test_fix", 0) + 1
    return {"stage_retries": retries}


def _build_fix_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build context for bug fixer with source files and test results."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"source_files": "(no source files)"}

    ws = Workspace(workspace_path)
    files = [f for f in ws.list_files() if not f.startswith("tests/")]
    return {"source_files": collect_file_contents(ws, files)}


# ---------------------------------------------------------------------------
# Degeneracy detection nodes
# ---------------------------------------------------------------------------


def _check_degeneracy(state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic scan for catastrophically degenerate .py files.

    Checks for:
    1. Repetition: >30% of non-blank lines are duplicates of a single line
    2. Syntax errors: compile() fails (truncation, unclosed brackets, etc.)
    3. Stub-only: all function/method bodies are just pass/Ellipsis/raise NotImplementedError
    """
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"degenerate_files": "[]", "degeneracy_detected": False}

    ws = Workspace(workspace_path)
    py_files = [
        f for f in ws.list_files()
        if f.endswith(".py")
        and not f.startswith("tests/")
        and not f.startswith(".venv/")
        and f != "acceptance_test.py"
        and f != "setup.py"
    ]

    issues: list[dict[str, str]] = []

    for py_file in py_files:
        try:
            content = ws.read_file(py_file)
        except Exception:
            continue

        if not content.strip():
            continue

        # Check 1: Repetition — >30% of non-blank lines are the same line
        lines = [line for line in content.splitlines() if line.strip()]
        if len(lines) > 10:
            counts = Counter(lines)
            top_line, top_count = counts.most_common(1)[0]
            if top_count / len(lines) > 0.30:
                issues.append({
                    "file": py_file,
                    "issue": "repetition",
                    "detail": f"{top_count}/{len(lines)} lines ({top_count*100//len(lines)}%) are: {top_line[:80]}",
                })
                continue  # no need to check further

        # Check 2: Syntax errors via compile()
        try:
            compile(content, py_file, "exec")
        except SyntaxError as exc:
            issues.append({
                "file": py_file,
                "issue": "syntax_error",
                "detail": f"{exc.msg} (line {exc.lineno})",
            })
            continue

        # Check 3: Stub-only bodies — all function/method bodies are pass/Ellipsis/raise
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue  # already caught above but just in case

        func_defs = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if len(func_defs) >= 2:
            stub_count = 0
            for func in func_defs:
                body = func.body
                # Filter out docstrings
                stmts = [
                    s for s in body
                    if not (isinstance(s, ast.Expr) and isinstance(s.value, (ast.Constant, ast.Str)))
                ]
                if not stmts:
                    stub_count += 1
                    continue
                if all(_is_stub_stmt(s) for s in stmts):
                    stub_count += 1
            if stub_count == len(func_defs):
                issues.append({
                    "file": py_file,
                    "issue": "stub_only",
                    "detail": f"All {len(func_defs)} functions have stub-only bodies (pass/Ellipsis/raise NotImplementedError)",
                })

    return {
        "degenerate_files": json.dumps(issues, indent=2),
        "degeneracy_detected": len(issues) > 0,
    }


def _is_stub_stmt(node: ast.stmt) -> bool:
    """Return True if a statement is a stub: pass, Ellipsis, or raise NotImplementedError."""
    if isinstance(node, ast.Pass):
        return True
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
        if node.value.value is ...:
            return True
    if isinstance(node, ast.Raise):
        exc = node.exc
        if exc is not None:
            # raise NotImplementedError or raise NotImplementedError(...)
            if isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                return True
            if isinstance(exc, ast.Call):
                func = exc.func
                if isinstance(func, ast.Name) and func.id == "NotImplementedError":
                    return True
    return False


def _degeneracy_decision(state: dict[str, Any]) -> str:
    """Route based on degeneracy check results."""
    if not state.get("degeneracy_detected", False):
        return "clean"
    retries = state.get("stage_retries", {}).get("regen", 0)
    if retries >= 2:
        return "force_pass"
    return "degenerate"


def _build_regen_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build context for code regenerator: healthy files + degenerate file list."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"healthy_files": "(no files)"}

    # Parse which files are degenerate
    try:
        degenerate_list = json.loads(state.get("degenerate_files", "[]"))
    except (json.JSONDecodeError, TypeError):
        degenerate_list = []
    degenerate_paths = {entry["file"] for entry in degenerate_list}

    ws = Workspace(workspace_path)
    all_files = [
        f for f in ws.list_files()
        if f.endswith(".py")
        and not f.startswith("tests/")
        and not f.startswith(".venv/")
        and f != "acceptance_test.py"
    ]

    healthy_files = [f for f in all_files if f not in degenerate_paths]
    if ws.file_exists("requirements.txt"):
        healthy_files.append("requirements.txt")

    return {"healthy_files": collect_file_contents(ws, healthy_files)}


def _process_regen(state: dict[str, Any]) -> dict[str, Any]:
    """Write regenerated files to workspace and bump retry counter."""
    from summon.workspace import normalize_file_entry

    result = state.get("_regen_result", {})
    files = result.get("files", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and files:
        ws = Workspace(workspace_path)
        for f in files:
            path, content = normalize_file_entry(f)
            if path and content:
                ws.write_file(path, content)

    retries = dict(state.get("stage_retries", {}))
    retries["regen"] = retries.get("regen", 0) + 1
    return {"stage_retries": retries}


# ---------------------------------------------------------------------------
# Import validation nodes
# ---------------------------------------------------------------------------


def _validate_imports(state: dict[str, Any]) -> dict[str, Any]:
    """Run 'python -c \"import X\"' for every .py file in the workspace."""
    import os

    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"import_errors": "", "import_validation_passing": True}

    language = state.get("spec", {}).get("language", "python")
    if language != "python":
        return {"import_errors": "", "import_validation_passing": True}

    ws = Workspace(workspace_path)
    py_files = [
        f for f in ws.list_files()
        if f.endswith(".py")
        and not f.startswith("tests/")
        and not f.startswith(".venv/")
        and f != "acceptance_test.py"
        and f != "setup.py"
        and not f.endswith("__init__.py")
    ]

    venv_python = os.path.join(workspace_path, ".venv", "bin", "python")
    python_cmd = venv_python if os.path.exists(venv_python) else "python"

    env = os.environ.copy()
    env["PYTHONPATH"] = workspace_path

    errors = []
    for py_file in py_files:
        module_name = py_file.replace("/", ".").replace(".py", "")
        result = run_command(
            f'{python_cmd} -c "import {module_name}" 2>&1',
            cwd=workspace_path,
            timeout=30,
            env=env,
        )
        if not result.success:
            errors.append(f"--- {py_file} (import {module_name}) ---\n{result.output}")

    error_text = "\n\n".join(errors) if errors else ""
    return {
        "import_errors": error_text,
        "import_validation_passing": len(errors) == 0,
    }


def _import_decision(state: dict[str, Any]) -> str:
    """Route based on import validation results."""
    if state.get("import_validation_passing", False):
        return "passing"
    retries = state.get("stage_retries", {}).get("import_fix", 0)
    if retries >= 3:
        return "force_pass"
    return "failing"


def _build_import_fix_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build context for import fixer with all source files."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"import_fix_source_files": "(no source files)"}

    ws = Workspace(workspace_path)
    files = [
        f for f in ws.list_files()
        if (f.endswith(".py") or f == "requirements.txt")
        and not f.startswith(".venv/")
        and f != "acceptance_test.py"
    ]
    return {"import_fix_source_files": collect_file_contents(ws, files)}


def _process_import_fixes(state: dict[str, Any]) -> dict[str, Any]:
    """Apply import fixes to workspace."""
    from summon.workspace import normalize_file_entry

    result = state.get("_import_fix_result", {})
    fixes = result.get("fixes", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and fixes:
        ws = Workspace(workspace_path)
        for fix in fixes:
            path, content = normalize_file_entry(fix)
            if path and content:
                ws.write_file(path, content)

    retries = dict(state.get("stage_retries", {}))
    retries["import_fix"] = retries.get("import_fix", 0) + 1
    return {"stage_retries": retries}


# ---------------------------------------------------------------------------
# Adversarial testing nodes
# ---------------------------------------------------------------------------


def _build_adversarial_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build project files context for adversarial test writer."""
    return _build_project_files_context(state)


def _process_adversarial_tests(state: dict[str, Any]) -> dict[str, Any]:
    """Write adversarial test file to workspace."""
    result = state.get("_adversarial_test_result", {})
    test_code = result.get("test_code", "")
    test_path = result.get("test_file_path", "tests/test_adversarial.py")
    workspace_path = state.get("workspace_path", "")

    if workspace_path and test_code:
        ws = Workspace(workspace_path)
        ws.write_file(test_path, test_code)

    return {"adversarial_test_code": test_code}


def _run_adversarial_tests(state: dict[str, Any]) -> dict[str, Any]:
    """Run only the adversarial tests (not the full suite)."""
    import os

    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"adversarial_test_results": "No workspace", "adversarial_tests_passing": False}

    venv_python = os.path.join(workspace_path, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        cmd = f"{venv_python} -m pytest tests/test_adversarial.py -v --tb=short 2>&1"
    else:
        cmd = "python -m pytest tests/test_adversarial.py -v --tb=short 2>&1"

    env = os.environ.copy()
    pypath_parts = [workspace_path]
    src_dir = os.path.join(workspace_path, "src")
    if os.path.isdir(src_dir):
        pypath_parts.append(src_dir)
    env["PYTHONPATH"] = os.pathsep.join(pypath_parts)

    result = run_command(cmd, cwd=workspace_path, timeout=120, env=env)
    output = result.output[:4000]

    passing = result.success
    if passing:
        import re
        fail_patterns = [
            r'\d+ failed',
            r'^FAILED ',
            r'^ERRORS$',
            r'failures=\d*[1-9]',
            r'Tests:\s+\d+ failed',
        ]
        for pattern in fail_patterns:
            if re.search(pattern, output, re.MULTILINE):
                passing = False
                break

    return {
        "adversarial_test_results": output,
        "adversarial_tests_passing": passing,
    }


def _adversarial_decision(state: dict[str, Any]) -> str:
    """Route based on adversarial test results."""
    if state.get("adversarial_tests_passing", False):
        return "passing"
    retries = state.get("stage_retries", {}).get("adversarial_fix", 0)
    if retries >= 3:
        return "force_pass"
    return "failing"


def _build_adversarial_fix_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build context for adversarial fixer with source files."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"source_files": "(no source files)"}

    ws = Workspace(workspace_path)
    files = [
        f for f in ws.list_files()
        if f.endswith(".py")
        and not f.startswith("tests/")
        and not f.startswith(".venv/")
        and f != "acceptance_test.py"
    ]
    return {"source_files": collect_file_contents(ws, files)}


def _process_adversarial_fixes(state: dict[str, Any]) -> dict[str, Any]:
    """Apply adversarial bug fixes to workspace and bump retry counter."""
    from summon.workspace import normalize_file_entry

    result = state.get("_adversarial_fix_result", {})
    fixes = result.get("fixes", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and fixes:
        ws = Workspace(workspace_path)
        for fix in fixes:
            path, content = normalize_file_entry(fix)
            if path and content:
                ws.write_file(path, content)

    retries = dict(state.get("stage_retries", {}))
    retries["adversarial_fix"] = retries.get("adversarial_fix", 0) + 1
    return {"stage_retries": retries}


# ---------------------------------------------------------------------------
# Acceptance testing nodes
# ---------------------------------------------------------------------------


def _rebuild_context(state: dict[str, Any]) -> dict[str, Any]:
    """Rebuild project files context after tests pass (for acceptance testing).

    Excludes test files to keep prompt size manageable — acceptance criteria
    only need the source code and spec.
    """
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"project_files": "(no files yet)"}

    ws = Workspace(workspace_path)
    files = [
        f for f in ws.list_files()
        if not f.startswith(".venv/")
        and not f.startswith("__pycache__/")
        and "__pycache__/" not in f
        and not f.endswith(".pyc")
        and not f.startswith("tests/")
        and f != "acceptance_test.py"
    ]
    return {"project_files": collect_file_contents(ws, files)}


def _process_acceptance_criteria(state: dict[str, Any]) -> dict[str, Any]:
    """Extract acceptance criteria from LLM result."""
    result = state.get("_acceptance_gen_result", {})
    criteria = result.get("criteria", [])
    return {"acceptance_criteria": json.dumps(criteria, indent=2) if criteria else "[]"}


def _process_acceptance_tests(state: dict[str, Any]) -> dict[str, Any]:
    """Write acceptance test script to workspace."""
    result = state.get("_acceptance_test_gen_result", {})
    script = result.get("test_script", "")
    script_path = result.get("test_file_path", "acceptance_test.py")
    workspace_path = state.get("workspace_path", "")

    if workspace_path and script:
        ws = Workspace(workspace_path)
        ws.write_file(script_path, script)

    return {"acceptance_test_script": script}


def _run_acceptance_tests(state: dict[str, Any]) -> dict[str, Any]:
    """Run the acceptance test script."""
    import os

    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {
            "acceptance_test_results": "No workspace",
            "acceptance_tests_passing": False,
        }

    ws = Workspace(workspace_path)
    if not ws.file_exists("acceptance_test.py"):
        return {
            "acceptance_test_results": "No acceptance test script found",
            "acceptance_tests_passing": True,  # Skip if no script
        }

    venv_python = os.path.join(workspace_path, ".venv", "bin", "python")
    python_cmd = venv_python if os.path.exists(venv_python) else "python"

    env = os.environ.copy()
    env["PYTHONPATH"] = workspace_path

    result = run_command(
        f"{python_cmd} acceptance_test.py 2>&1",
        cwd=workspace_path,
        timeout=300,
        env=env,
    )
    output = result.output[:4000]

    # Parse results: look for "ACCEPTANCE RESULTS: X passed, Y failed"
    passing = result.success
    if "ACCEPTANCE FAIL:" in output:
        passing = False

    return {
        "acceptance_test_results": output,
        "acceptance_tests_passing": passing,
    }


def _acceptance_decision(state: dict[str, Any]) -> str:
    """Route based on acceptance test results."""
    if state.get("acceptance_tests_passing", False):
        return "passing"
    retries = state.get("stage_retries", {}).get("acceptance_fix", 0)
    if retries >= 2:
        return "force_pass"
    return "failing"


def _build_acceptance_fix_context(state: dict[str, Any]) -> dict[str, Any]:
    """Build context for acceptance fixer with source files and test results."""
    workspace_path = state.get("workspace_path", "")
    if not workspace_path:
        return {"source_files": "(no source files)"}

    ws = Workspace(workspace_path)
    files = [
        f for f in ws.list_files()
        if f.endswith(".py")
        and not f.startswith("tests/")
        and not f.startswith(".venv/")
        and f != "acceptance_test.py"
    ]
    return {"source_files": collect_file_contents(ws, files)}


def _process_acceptance_fixes(state: dict[str, Any]) -> dict[str, Any]:
    """Apply acceptance test fixes to workspace."""
    from summon.workspace import normalize_file_entry

    result = state.get("_acceptance_fix_result", {})
    fixes = result.get("fixes", [])
    workspace_path = state.get("workspace_path", "")

    if workspace_path and fixes:
        ws = Workspace(workspace_path)
        for fix in fixes:
            path, content = normalize_file_entry(fix)
            if path and content:
                ws.write_file(path, content)

    retries = dict(state.get("stage_retries", {}))
    retries["acceptance_fix"] = retries.get("acceptance_fix", 0) + 1
    return {"stage_retries": retries}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def create_stage5_graph(config: SummonConfig) -> StateGraph:
    """Build the Stage 5 subgraph:

    integrate → process_integration → install_deps
      → check_degeneracy
        ├─ clean → validate_imports
        ├─ degenerate → build_regen_context → regenerate → process_regen → install_deps
        └─ force_pass (2 retries) → validate_imports
      → validate_imports ←── (import fix loop, 3 retries)
      → build_context → write_tests → process_tests
      → run_tests ←── (unit test fix loop, 3 retries)
      → build_adversarial_context → write_adversarial_tests → process_adversarial_tests
      → run_adversarial_tests ←── (adversarial fix loop, 3 retries)
      → rebuild_context → generate_acceptance_criteria → process_criteria
      → generate_acceptance_tests → process_acceptance_tests
      → run_acceptance_tests ←── (acceptance fix loop, 2 retries)
      → END
    """
    graph = StateGraph(SummonState)

    # --- Integration ---
    graph.add_node("build_integration_context", _build_integration_context)
    graph.add_node("integrate", create_integrator_node(config))
    graph.add_node("process_integration", _process_integration)
    graph.add_node("install_deps", _install_deps)

    # --- Degeneracy detection & regeneration ---
    graph.add_node("check_degeneracy", _check_degeneracy)
    graph.add_node("build_regen_context", _build_regen_context)
    graph.add_node("regenerate_degenerate", create_code_regenerator_node(config))
    graph.add_node("process_regen", _process_regen)

    # --- Import validation loop ---
    graph.add_node("validate_imports", _validate_imports)
    graph.add_node("build_import_fix_context", _build_import_fix_context)
    graph.add_node("fix_imports", create_import_fixer_node(config))
    graph.add_node("process_import_fixes", _process_import_fixes)

    # --- Unit test loop ---
    graph.add_node("build_context", _build_project_files_context)
    graph.add_node("write_tests", create_test_writer_node(config))
    graph.add_node("process_tests", _process_tests)
    graph.add_node("run_tests", _run_tests)
    graph.add_node("build_fix_context", _build_fix_context)
    graph.add_node("fix_bugs", create_bug_fixer_node(config))
    graph.add_node("process_fixes", _process_fixes)

    # --- Adversarial test loop ---
    graph.add_node("build_adversarial_context", _build_adversarial_context)
    graph.add_node("write_adversarial_tests", create_adversarial_tester_node(config))
    graph.add_node("process_adversarial_tests", _process_adversarial_tests)
    graph.add_node("run_adversarial_tests", _run_adversarial_tests)
    graph.add_node("build_adversarial_fix_context", _build_adversarial_fix_context)
    graph.add_node("fix_adversarial_bugs", create_adversarial_fixer_node(config))
    graph.add_node("process_adversarial_fixes", _process_adversarial_fixes)

    # --- Acceptance test loop ---
    graph.add_node("rebuild_context", _rebuild_context)
    graph.add_node("generate_acceptance_criteria", create_acceptance_criteria_gen_node(config))
    graph.add_node("process_criteria", _process_acceptance_criteria)
    graph.add_node("generate_acceptance_tests", create_acceptance_test_gen_node(config))
    graph.add_node("process_acceptance_tests", _process_acceptance_tests)
    graph.add_node("run_acceptance_tests", _run_acceptance_tests)
    graph.add_node("build_acceptance_fix_context", _build_acceptance_fix_context)
    graph.add_node("fix_acceptance", create_acceptance_fixer_node(config))
    graph.add_node("process_acceptance_fixes", _process_acceptance_fixes)

    # === Edges ===

    # Integration
    graph.set_entry_point("build_integration_context")
    graph.add_edge("build_integration_context", "integrate")
    graph.add_edge("integrate", "process_integration")
    graph.add_edge("process_integration", "install_deps")

    # Degeneracy check (between install_deps and validate_imports)
    graph.add_edge("install_deps", "check_degeneracy")
    graph.add_conditional_edges(
        "check_degeneracy",
        _degeneracy_decision,
        {
            "clean": "validate_imports",
            "degenerate": "build_regen_context",
            "force_pass": "validate_imports",
        }
    )
    graph.add_edge("build_regen_context", "regenerate_degenerate")
    graph.add_edge("regenerate_degenerate", "process_regen")
    graph.add_edge("process_regen", "install_deps")

    # Import validation loop
    graph.add_conditional_edges(
        "validate_imports",
        _import_decision,
        {
            "passing": "build_context",
            "failing": "build_import_fix_context",
            "force_pass": "build_context",
        }
    )
    graph.add_edge("build_import_fix_context", "fix_imports")
    graph.add_edge("fix_imports", "process_import_fixes")
    graph.add_edge("process_import_fixes", "install_deps")

    # Unit test loop
    graph.add_edge("build_context", "write_tests")
    graph.add_edge("write_tests", "process_tests")
    graph.add_edge("process_tests", "run_tests")
    graph.add_conditional_edges(
        "run_tests",
        _test_decision,
        {
            "passing": "build_adversarial_context",
            "failing": "build_fix_context",
            "force_pass": "build_adversarial_context",
        }
    )
    graph.add_edge("build_fix_context", "fix_bugs")
    graph.add_edge("fix_bugs", "process_fixes")
    graph.add_edge("process_fixes", "run_tests")

    # Adversarial test loop
    graph.add_edge("build_adversarial_context", "write_adversarial_tests")
    graph.add_edge("write_adversarial_tests", "process_adversarial_tests")
    graph.add_edge("process_adversarial_tests", "run_adversarial_tests")
    graph.add_conditional_edges(
        "run_adversarial_tests",
        _adversarial_decision,
        {
            "passing": "rebuild_context",
            "failing": "build_adversarial_fix_context",
            "force_pass": "rebuild_context",
        }
    )
    graph.add_edge("build_adversarial_fix_context", "fix_adversarial_bugs")
    graph.add_edge("fix_adversarial_bugs", "process_adversarial_fixes")
    graph.add_edge("process_adversarial_fixes", "run_adversarial_tests")

    # Acceptance test loop
    graph.add_edge("rebuild_context", "generate_acceptance_criteria")
    graph.add_edge("generate_acceptance_criteria", "process_criteria")
    graph.add_edge("process_criteria", "generate_acceptance_tests")
    graph.add_edge("generate_acceptance_tests", "process_acceptance_tests")
    graph.add_edge("process_acceptance_tests", "run_acceptance_tests")
    graph.add_conditional_edges(
        "run_acceptance_tests",
        _acceptance_decision,
        {
            "passing": END,
            "failing": "build_acceptance_fix_context",
            "force_pass": END,
        }
    )
    graph.add_edge("build_acceptance_fix_context", "fix_acceptance")
    graph.add_edge("fix_acceptance", "process_acceptance_fixes")
    graph.add_edge("process_acceptance_fixes", "run_acceptance_tests")

    return graph
