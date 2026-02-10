"""Prompt templates for Stage 5: Testing."""

INTEGRATOR = """\
You are integrating independently-built components into a cohesive project.

Spec:
{spec}

HLD:
{hld}

Component results:
{component_results}

Review all component files and produce the GLUE that makes them work together:

1. Fix any import path mismatches between components
2. Write a requirements.txt listing every third-party package the code imports
3. Write the main entry point (e.g. main.py or app.py) if one doesn't exist
4. Write any missing __init__.py files
5. Ensure the user can actually run the project with: \
   pip install -r requirements.txt && python main.py (or the appropriate command)

Return a JSON object with a "files" array — one entry per file to create or overwrite:
{{
  "files": [
    {{"path": "requirements.txt", "content": "yt-dlp\\nopenai-whisper\\nclick"}},
    {{"path": "main.py", "content": "...full file content..."}},
    {{"path": "__init__.py", "content": ""}}
  ],
  "issues": ["integration issues found"]
}}

IMPORTANT: Include EVERY additional file needed. Do NOT skip requirements.txt. \
Include the complete content for each file — no placeholders.
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
