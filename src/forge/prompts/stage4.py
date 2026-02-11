"""Prompt templates for Stage 4: Implementation."""

LLD_WRITER = """\
You are writing a low-level design for a single component.

Spec:
{spec}

Component:
{component}

Full HLD context:
{hld}

Write a detailed implementation plan covering:
1. File-by-file breakdown with class/function signatures
2. Concrete algorithm choices — specify which libraries to use and how
3. Error handling strategy
4. How this component interfaces with dependencies
5. For each function: what it actually does step by step, not just its name

Be specific about which libraries to use and how. Name the exact package and API calls — \
no hand-waving.

IMPORTANT CONSTRAINTS:
- All files go in the project root — no src/ subdirectory.
- Use plain imports: "from models import X", not "from src.models import X".
- Do NOT redefine types that belong in the shared models.py — import them.

Return as JSON:
{{"lld_summary": "detailed implementation plan text"}}
"""

CODER = """\
You are a senior software engineer. Write COMPLETE, WORKING code. \
Every function must have a real implementation. No placeholders. No stubs. \
No "TODO" comments. No "pass" bodies. No "placeholder" text.

Spec:
{spec}

Component:
{component}

Low-Level Design:
{_lld_result}

HLD context (for interfaces):
{hld}

Write the FULL implementation for each file in this component.

CRITICAL RULES:
1. Every function must contain real, working logic — NOT placeholders or stubs
2. Use real third-party libraries where needed
3. Include ALL imports at the top of each file
4. Add type hints to all function signatures
5. Handle errors with try/except and meaningful error messages
6. If a function needs to call an external API or tool, write the actual call
7. Follow the spec's language: {language}
8. Do NOT write tests — those come in Stage 5

IMPORT AND STRUCTURE RULES:
9. All files go in the project ROOT — no src/ subdirectory, no nested packages.
10. Use plain imports: "from models import MyClass", "from downloader import func".
   NEVER use "from src." or package-qualified imports.
11. Do NOT redefine data classes/types that belong in models.py or another component. \
    Import them instead. Check the HLD's "shared_types" and other components' interfaces.
12. If the HLD says a type is in models.py, import it: "from models import TypeName".
13. If the HLD's interfaces list a function like "download_video(url) -> str", \
    you MUST define it as a top-level module function, NOT as a method on a class. \
    Other modules will import it by name: "from downloader import download_video".

Return as JSON:
{{
  "files": [
    {{"path": "filename.py", "content": "full file content"}}
  ]
}}
"""

CODE_REVIEWER = """\
You are a strict senior code reviewer. Your job is to REJECT code that contains \
placeholders, stubs, TODO comments, or incomplete implementations.

Spec:
{spec}

Component design:
{component}

Implementation files:
{_code_result}

Review STRICTLY for:
1. COMPLETENESS — Does every function have a real implementation? \
   Any "placeholder", "TODO", "pass", or "NotImplementedError" is an automatic FAIL.
2. Correctness — Does it actually implement the component's requirements?
3. Interface compliance — Does it match the HLD interfaces?
4. Working imports — Are all imported packages real and used correctly?
5. Error handling — Are errors caught and reported meaningfully?

Return JSON:
{{
  "approved": true/false,
  "issues": ["critical issues that must be fixed"],
  "suggestions": ["nice-to-have improvements"]
}}

Set approved=false if ANY function body is a placeholder, stub, or TODO.
"""
