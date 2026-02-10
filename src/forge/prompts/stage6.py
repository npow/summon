"""Prompt templates for Stage 6: Package & Release."""

PACKAGER = """\
You are a packaging expert. Create distribution-ready package configuration.

Spec:
{spec}

Project files:
{project_files}

Create all necessary packaging files for the project's language:
- Python: pyproject.toml, setup.cfg, MANIFEST.in
- TypeScript: package.json, tsconfig.json
- Go: go.mod

Return JSON:
{{
  "files": [
    {{"path": "pyproject.toml", "content": "..."}}
  ]
}}
"""

DOCS_WRITER = """\
You are a technical writer. Create documentation for this project.

Spec:
{spec}

Project files:
{project_files}

Create a comprehensive README.md that includes:
1. Project name and one-liner from spec
2. Installation instructions
3. Usage examples (CLI commands or API usage)
4. Configuration options
5. Contributing guide (brief)
6. License (MIT)

Return JSON:
{{
  "readme": "full README.md content",
  "changelog": "## 0.1.0\\n- Initial release\\n- features..."
}}
"""

GITHUB_AGENT = """\
You are setting up a GitHub repository for this project.

Spec:
{spec}

Project structure:
{project_files}

Generate the necessary GitHub configuration files:
1. .gitignore (language-appropriate)
2. .github/workflows/ci.yml (test + lint on push)
3. LICENSE (MIT)

Return JSON:
{{
  "files": [
    {{"path": ".gitignore", "content": "..."}},
    {{"path": ".github/workflows/ci.yml", "content": "..."}},
    {{"path": "LICENSE", "content": "..."}}
  ]
}}
"""

PUBLISHER = """\
You are publishing a package to a registry.

Spec:
{spec}

Package files:
{package_files}

Determine the publish command and configuration needed:
- Python/PyPI: twine upload
- npm: npm publish
- Go: git tag

Return JSON:
{{
  "publish_command": "the command to run",
  "registry_url": "URL where package will be available",
  "pre_publish_checks": ["check 1", "check 2"]
}}
"""
