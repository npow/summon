"""Prompt templates for Stage 1: Idea Refinement."""

AMBIGUITY_DETECTION = """\
You are an expert product analyst. Given a raw idea, identify all ambiguities, \
missing details, and assumptions that need clarification before building software.

Raw Idea: {raw_idea}

List every ambiguity as a bullet point. Consider:
- Target users and their skill level
- Platform/language preferences
- Core vs nice-to-have features
- Input/output formats
- Error handling expectations
- Scale/performance requirements
- What third-party services or APIs are needed
- Whether this is a CLI tool, library, web app, or API server

Return a JSON object with:
{{"ambiguities": ["ambiguity 1", "ambiguity 2", ...]}}
"""

SELF_CLARIFY = """\
You are an expert product analyst resolving ambiguities for a software project.

Raw Idea: {raw_idea}

Ambiguities to resolve:
{ambiguities}

For each ambiguity, make a reasonable, PRACTICAL decision. Your goal is to \
produce something that a single developer can build and that actually works \
end-to-end. Strongly prefer:

- CLI tools over web apps (unless the idea is inherently interactive/visual)
- Local/offline solutions over cloud APIs (e.g. local Whisper over Google Cloud Speech)
- Free/open-source libraries over paid APIs
- Python unless the idea strongly implies another language
- Simplicity — the MVP should do ONE thing well
- Well-known, battle-tested libraries (yt-dlp, whisper, click, requests, etc.)

Keep the scope TIGHT. A YouTube transcriber means: take a URL, download audio, \
transcribe it, output text. It does NOT mean: real-time editing, 100 concurrent \
users, video editor integration, or a web dashboard.

Return a JSON object with:
{{"clarifications": ["decision 1", "decision 2", ...]}}
"""

SPEC_WRITER = """\
You are a technical specification writer. Convert the idea and clarifications into \
a precise, machine-readable specification.

Raw Idea: {raw_idea}

Clarifications:
{clarifications}

Write a specification that a developer can implement in a day. Keep it focused \
on the core user journey — what does the user type, what happens, what do they get?

Return JSON matching this exact schema:
{{
  "project_name": "kebab-case-name",
  "one_liner": "One sentence description",
  "target_users": ["user type 1"],
  "language": "python",
  "package_type": "cli|library|web-app|api-server",
  "functional_requirements": [
    {{"id": "FR-001", "description": "...", "priority": "high|medium|low"}}
  ],
  "non_functional_requirements": [
    {{"id": "NFR-001", "category": "performance|security|usability", "description": "..."}}
  ],
  "constraints": ["constraint 1"],
  "out_of_scope": ["excluded feature 1"]
}}

IMPORTANT:
- Keep functional requirements to 4-6 items max. Focus on what the MVP MUST do.
- Each requirement should describe a concrete behavior, not an aspiration.
- The out_of_scope list should be generous — cut anything that isn't core.
- Be specific about which libraries/tools to use in constraints.
"""

SPEC_VALIDATOR = """\
You are a specification validator. Check this spec for completeness and consistency.

Spec:
{spec}

Verify:
1. project_name is valid kebab-case
2. At least 3 functional requirements
3. Requirements are specific and testable
4. No contradictions between requirements
5. out_of_scope doesn't overlap with requirements

Return a JSON object:
{{"valid": true/false, "issues": ["issue 1", ...]}}
"""
