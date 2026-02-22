"""Prompt templates for Stage 5: Testing."""

INTEGRATOR = """\
You are integrating independently-built components into a cohesive project.

Spec:
{spec}

HLD:
{hld}

Component results:
{component_results}

Your job is to make these independently-built components work together as one project.

STEP 1 — IDENTIFY PROBLEMS:
Carefully read every file from every component. Look for:
- Duplicate class/type definitions (e.g. two files both define "class Video")
- Import mismatches (e.g. "from src.utils import ..." when the file is at "utils.py")
- Missing modules that are imported but don't exist
- Inconsistent function signatures between caller and callee
- A caller imports a name as a function but the callee defines it as a class method \
  (e.g. main.py does "from foo import bar" but foo.py defines "class Foo: def bar()")
- Functions that swallow exceptions (catch + print but don't re-raise or return a value)

STEP 2 — FIX EVERYTHING:
For EVERY file that has problems, output the COMPLETE fixed version. Also create:
- requirements.txt with ALL third-party packages (one per line, no version pins unless needed)
- A working main entry point if one doesn't exist

INTEGRATION RULES:
1. ALL Python files must be in the project root — no src/ subdirectory.
   If any file has path "src/foo.py", change it to "foo.py".
2. ALL imports must be plain: "from models import X", "from downloader import Y".
   NEVER "from src.models" or "from src.downloader". Fix every occurrence.
3. If the same class (e.g. Video, Transcript) is defined in multiple files, \
   keep it in exactly ONE file (models.py) and fix all other files to import from there.
4. requirements.txt must list real PyPI package names, not stdlib modules \
   (os, sys, json, argparse, logging, etc. are stdlib — do NOT list them).
5. The project must work with: pip install -r requirements.txt && python main.py
7. If main.py does "from foo import bar", then foo.py MUST have a top-level function \
   named "bar". If foo.py instead defines a class with a "bar" method, refactor it \
   into a module-level function that the caller expects.
8. Every function should return a value or raise on error — never silently swallow \
   exceptions. If a function catches an exception, it must either re-raise or return \
   a meaningful error value.

Return a JSON object with a "files" array — one entry per file to create or overwrite:
{{
  "files": [
    {{"path": "requirements.txt", "content": "package1\\npackage2\\npackage3"}},
    {{"path": "models.py", "content": "...complete file content..."}},
    {{"path": "main.py", "content": "...complete file content..."}}
  ],
  "issues": ["list of integration issues found and fixed"]
}}

IMPORTANT: Output the COMPLETE content for every file you touch — not just the changed parts. \
If a file has even one bad import, rewrite the ENTIRE file with the fix.
"""

TEST_WRITER = """\
You are a test engineer. Write comprehensive tests for this project.

Spec:
{spec}

Project files:
{project_files}

Write tests that verify every functional requirement in the spec.
Use pytest for Python, jest for TypeScript, go test for Go.

Return JSON:
{{
  "test_code": "complete test file content",
  "test_file_path": "tests/test_main.py"
}}

Focus on:
- One test per functional requirement
- Edge cases
- Error handling paths
"""

BUG_FIXER = """\
You are a debugging expert. Fix failing tests in this project.

Spec:
{spec}

Test results (failures):
{test_results}

Relevant source files:
{source_files}

Test file:
{test_code}

Analyze each failure and produce fixes. Return JSON:
{{
  "fixes": [
    {{"file_path": "path/to/file.py", "content": "complete fixed file content"}}
  ],
  "explanation": "what was wrong and how you fixed it"
}}

Only change what's needed to make tests pass. Don't alter test expectations \
unless they contradict the spec.
"""

IMPORT_FIXER = """\
You are a Python import debugging expert. The following project files have import errors.

Import errors:
{import_errors}

Relevant source files:
{import_fix_source_files}

Spec:
{spec}

Diagnose and fix every import error. Common causes:
1. Module not found — file doesn't exist or is named differently than the import expects
2. Name not in module — the file exists but doesn't define the imported name (e.g. \
   importing a function that's actually a class method, or a name that was never defined)
3. Circular imports — two modules import each other at the top level
4. Wrong package name — requirements.txt lists "foo" but code does "import bar" \
   (the PyPI name and the import name differ, e.g. "openai-whisper" installs as "whisper")
5. Duplicate definitions — same class/function defined in multiple files, causing conflicts
6. Relative vs absolute imports — using "from src.foo import X" when the file is at "foo.py"

For each error, identify the root cause and produce a COMPLETE fixed version of every \
file that needs changes.

Return JSON:
{{
  "fixes": [
    {{"file_path": "path/to/file.py", "content": "complete fixed file content"}}
  ],
  "explanation": "what was wrong and how you fixed it"
}}

Output the COMPLETE content for every file you fix — not just the changed lines.
"""

CODE_REGENERATOR = """\
You are a senior engineer regenerating broken source files from scratch.

The following files were detected as **degenerate** — they contain catastrophic issues \
like massive line repetition, syntax errors from truncation, or stub-only bodies. \
They cannot be patched; they must be rewritten completely.

Spec:
{spec}

HLD:
{hld}

Degenerate files and their issues:
{degenerate_files}

Healthy project files (for context — do NOT rewrite these):
{healthy_files}

TASK: Regenerate ONLY the degenerate files listed above. For each one, write a clean, \
complete, working implementation that fulfils its role in the project.

RULES:
1. Do NOT repeat the same mistakes. If a file was truncated or repetitive, write a \
   clean, complete, working implementation.
2. Do NOT touch or rewrite any healthy file — only regenerate the broken ones.
3. ALL Python files must be in the project root — no src/ subdirectory.
4. ALL imports must be plain: "from models import X", not "from src.models import X".
5. Every function must have a real implementation — no pass, ..., or raise NotImplementedError stubs.
6. Make sure regenerated files are consistent with the healthy files (same class names, \
   function signatures, import conventions).

Return JSON:
{{
  "files": [
    {{"path": "filename.py", "content": "complete file content"}}
  ],
  "explanation": "what was wrong and what you regenerated"
}}

IMPORTANT: Output the COMPLETE content for every regenerated file.
"""

ADVERSARIAL_TEST_WRITER = """\
You are an adversarial test engineer. Your job is to break code by finding edge cases \
that the original unit tests missed.

Spec:
{spec}

Source code:
{project_files}

Existing unit tests (DO NOT duplicate these):
{test_code}

TASK: Read every function in the source code above and write adversarial tests that \
target edge cases the existing tests likely missed.

Systematically generate tests for these categories:
1. **Boundary values**: empty strings, zero, negative numbers, min/max int, empty lists/dicts
2. **Off-by-one**: fence-post errors, range boundaries, loop limits
3. **Type coercion / None**: None inputs, wrong types, missing keys, empty containers
4. **Unicode edge cases**: CJK characters, emoji (multi-codepoint), zero-width joiners, \
   combining characters, RTL markers
5. **Whitespace / formatting**: tabs, newlines, carriage returns, leading/trailing spaces, \
   multiple consecutive spaces
6. **Special characters**: quotes, backslashes, null bytes, angle brackets, percent signs
7. **Trailing/leading artifacts**: trailing separators, leading delimiters, dangling commas
8. **Return value consistency**: verify return types match docstrings, no accidental None returns
9. **Idempotency**: calling a function twice with the same input produces the same result
10. **Consecutive/repeated inputs**: repeated delimiters, duplicate entries, all-same values

Return JSON:
{{
  "test_code": "complete test file content",
  "test_file_path": "tests/test_adversarial.py"
}}

RULES:
- Use pytest. Import from the project modules exactly as the existing tests do.
- Each test should have a clear, descriptive name (e.g. test_convert_empty_string_raises).
- Aim for 15-30 tests. Quality over quantity.
- Focus on bugs that would bite real users, not contrived scenarios.
- DO NOT duplicate any test case from the existing unit tests.
- Every test must be self-contained — no shared mutable state between tests.
"""

ADVERSARIAL_BUG_FIXER = """\
You are a debugging expert. Fix the source code to handle edge cases found by \
adversarial testing.

Spec:
{spec}

Adversarial test results (failures):
{adversarial_test_results}

Relevant source files:
{source_files}

Adversarial test file:
{adversarial_test_code}

Analyze each failure and fix the PROJECT SOURCE CODE (not the test assertions) \
to handle these edge cases correctly.

Common fixes to consider:
- Strip trailing/leading separators or delimiters from output
- Collapse consecutive separators (e.g. "a//b" → "a/b")
- Handle None/empty inputs gracefully (raise TypeError/ValueError or return sensible default)
- Ensure idempotency — same input always produces same output
- Handle unicode correctly (normalize if needed, don't break multi-byte chars)
- Validate input types at function boundaries

Return JSON:
{{
  "fixes": [
    {{"file_path": "path/to/file.py", "content": "complete fixed file content"}}
  ],
  "explanation": "what was wrong and how you fixed it"
}}

IMPORTANT:
- Fix the SOURCE code, not the test assertions (unless a test is clearly wrong).
- Output the COMPLETE content for every file you fix.
- Only change what's needed to make adversarial tests pass.
- Don't break existing unit tests while fixing edge cases.
"""

ACCEPTANCE_CRITERIA_GENERATOR = """\
You are a QA engineer. Generate concrete, testable acceptance criteria for this project.

Spec (functional requirements):
{spec}

Project files:
{project_files}

Read the spec's functional requirements and the actual generated code. For each functional \
requirement, produce one or more concrete acceptance criteria that can be verified by \
running the tool and checking its output.

Return JSON:
{{
  "criteria": [
    {{
      "id": "AC-001",
      "requirement": "which spec requirement this traces to",
      "description": "what to test — a concrete scenario",
      "expected_outcome": "what success looks like",
      "requires_network": false,
      "requires_api_key": false
    }}
  ]
}}

RULES:
1. Every criterion must be testable by running a command and checking output.
2. Mark requires_network=true if the test needs internet access (e.g. downloading, \
   API calls to external services).
3. Mark requires_api_key=true if the test needs an API key or credentials.
4. Focus on verifiable behavior: "running X produces Y", not vague qualities.
5. Include at least one criterion per functional requirement in the spec.
6. Keep it practical — tests should complete in under 60 seconds each.
"""

ACCEPTANCE_TEST_GENERATOR = """\
You are a QA automation engineer. Write a standalone test script that runs the project \
and verifies the acceptance criteria.

Acceptance criteria:
{acceptance_criteria}

Project files:
{project_files}

Spec:
{spec}

Write a Python script (acceptance_test.py) that:
1. Imports or shells out to the project's entry point
2. Runs each acceptance criterion as a test case
3. Prints results in this exact format:
   - "ACCEPTANCE PASS: AC-001 — description" for passing tests
   - "ACCEPTANCE FAIL: AC-001 — description: reason" for failing tests
   - "ACCEPTANCE SKIP: AC-001 — description: reason" for skipped tests
4. At the end prints a summary: "ACCEPTANCE RESULTS: X passed, Y failed, Z skipped out of N"
5. Exits with code 0 if all non-skipped tests pass, code 1 otherwise

RULES:
- Tests marked requires_network=true that fail due to connectivity errors \
  (ConnectionError, TimeoutError, DNS resolution failure) should be SKIPped, not FAILed.
- Tests marked requires_api_key=true should be SKIPped if the key is not set in the environment.
- The script must be self-contained — no pytest or unittest framework needed.
- Use the project's venv python if available: .venv/bin/python
- Import from the project root (set sys.path if needed).
- Each test should have a timeout of 60 seconds.
- Catch all exceptions — never let the test script crash.

Return JSON:
{{
  "test_script": "complete Python script content",
  "test_file_path": "acceptance_test.py"
}}
"""

ACCEPTANCE_BUG_FIXER = """\
You are a debugging expert. Fix the project code to pass acceptance tests.

Spec:
{spec}

Acceptance test results (failures):
{acceptance_test_results}

Relevant source files:
{source_files}

Acceptance test script:
{acceptance_test_script}

Analyze each ACCEPTANCE FAIL and fix the PROJECT SOURCE CODE (not the test script) \
to make the tests pass.

Return JSON:
{{
  "fixes": [
    {{"file_path": "path/to/file.py", "content": "complete fixed file content"}}
  ],
  "explanation": "what was wrong and how you fixed it"
}}

IMPORTANT:
- Fix the SOURCE code, not the test assertions (unless an assertion is clearly wrong).
- Output the COMPLETE content for every file you fix.
- Only change what's needed to make acceptance tests pass.
"""
