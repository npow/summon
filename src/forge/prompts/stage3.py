"""Prompt templates for Stage 3: High-Level Design."""

ARCHITECT = """\
You are a software architect. Create a high-level design from the spec and SDD.

Spec:
{spec}

SDD:
{sdd}

Create an HLD as JSON:
{{
  "project_name": "...",
  "module_diagram": "text diagram showing module relationships",
  "components": [
    {{
      "id": "comp-001",
      "name": "component name",
      "description": "what it does",
      "files": ["src/module.py"],
      "dependencies": [],
      "interfaces": ["function_name(args) -> return_type"]
    }}
  ],
  "shared_types": ["type definitions used across components"],
  "entry_point": "src/main.py"
}}

Break the system into 2-6 components that can be implemented independently.
Each component should have clear file boundaries and interfaces.
"""

COMPONENT_SPLITTER = """\
You are breaking down an HLD into independently implementable components.

HLD:
{hld}

For each component, verify:
1. It has clear input/output interfaces
2. Its file list doesn't overlap with other components
3. Dependencies between components are acyclic
4. Each component can be tested independently

Return the validated component list as JSON:
{{
  "components": [
    {{
      "id": "comp-001",
      "name": "...",
      "description": "...",
      "files": ["..."],
      "dependencies": ["comp-ids"],
      "interfaces": ["..."]
    }}
  ]
}}
"""
