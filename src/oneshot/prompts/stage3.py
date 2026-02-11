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
      "files": ["module.py"],
      "dependencies": [],
      "interfaces": ["function_name(args) -> return_type"]
    }}
  ],
  "shared_types": ["type definitions used across components"],
  "entry_point": "main.py"
}}

ARCHITECTURE RULES:
1. Use a FLAT file structure — all .py files in the project root. No src/ subdirectory, \
no nested packages. Example files: main.py, utils.py, core.py, models.py
2. Put ALL shared data classes / types in a single models.py file that other modules import from.
3. Every component's "interfaces" must list the exact function signatures other components call.
4. File lists MUST NOT overlap between components. If two components need the same type, \
it belongs in the shared models.py (assign it to exactly one component).
5. Break the system into 2-4 components for small CLI tools, more for larger projects.
6. The entry_point file (e.g. main.py) should be its own component that imports from the others.
7. Use plain imports between modules: "from models import MyClass", "from downloader import download".
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
