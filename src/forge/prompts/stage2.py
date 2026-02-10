"""Prompt templates for Stage 2: Product Planning (PRD + SDD)."""

PRD_WRITER = """\
You are a product manager. Create a Product Requirements Document from this spec.

Spec:
{spec}

Write a PRD as JSON:
{{
  "project_name": "...",
  "vision": "2-3 sentence product vision",
  "user_stories": [
    {{
      "id": "US-001",
      "persona": "developer",
      "action": "what they do",
      "benefit": "why they do it",
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }}
  ],
  "mvp_scope": ["US-001", "US-002"],
  "success_metrics": ["metric 1"]
}}

Focus on MVP. Every user story must trace back to a functional requirement in the spec.
"""

SDD_WRITER = """\
You are a software architect. Create a System Design Document from the spec and PRD.

Spec:
{spec}

PRD:
{prd}

Write an SDD as JSON:
{{
  "architecture_style": "monolith|microservices|serverless",
  "tech_stack": [
    {{"category": "framework", "choice": "...", "rationale": "..."}}
  ],
  "api_endpoints": [
    {{"method": "GET", "path": "/...", "description": "...", "request_schema": "", "response_schema": ""}}
  ],
  "data_models": ["Model description"],
  "directory_structure": "src/\\n  main.py\\n  ...",
  "dependencies": ["package1", "package2"]
}}

Keep it simple and aligned with the spec's language and package_type.
"""

CRITIC = """\
You are a technical critic reviewing planning documents for a software project.

Spec (immutable contract):
{spec}

PRD:
{prd}

SDD:
{sdd}

Evaluate the PRD and SDD against the spec. Check:
1. Every spec requirement is addressed
2. No scope creep beyond the spec
3. Tech choices are appropriate
4. Architecture matches the package_type
5. Dependencies are reasonable and minimal

Return JSON:
{{
  "approved": true/false,
  "issues": ["issue 1", ...],
  "suggestions": ["suggestion 1", ...]
}}

Be strict. Only approve if the planning documents faithfully implement the spec.
"""
