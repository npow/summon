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

Be specific. If this component needs to download YouTube audio, say "use yt-dlp \
to download, extract audio with ffmpeg". If it needs speech-to-text, say "use \
OpenAI Whisper (local model) via the openai-whisper package". No hand-waving.

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
2. Use real third-party libraries where needed (yt-dlp, whisper, flask, etc.)
3. Include ALL imports at the top of each file
4. Add type hints to all function signatures
5. Handle errors with try/except and meaningful error messages
6. If a function needs to call an external API or tool, write the actual call
7. Follow the spec's language: {language}
8. Do NOT write tests — those come in Stage 5

If you are unsure how to implement something, use the most common/standard \
library for that task and implement it fully. For example:
- YouTube download → yt-dlp
- Audio transcription → openai-whisper (local) or speech_recognition
- Web server → Flask or FastAPI
- File parsing → standard library or well-known packages

Return as JSON:
{{
  "files": [
    {{"path": "relative/path/to/file.py", "content": "full file content"}}
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
