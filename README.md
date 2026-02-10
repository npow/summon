# Forge

Autonomous idea-to-product pipeline powered by LangGraph. Takes a raw idea and produces a fully built, tested, and packaged project through 6 automated stages.

## Pipeline Stages

| # | Stage | Description |
|---|-------|-------------|
| 1 | Idea Refinement | Analyze ambiguities, resolve them, write spec |
| 2 | Product Planning | Generate PRD, SDD, critic review |
| 3 | High-Level Design | Architect components, split for parallel build |
| 4 | Implementation | LLD, code generation, code review per component |
| 5 | Testing | Integration tests, bug fixing |
| 6 | Package & Release | Packaging, docs, GitHub setup |

## Installation

```bash
uv sync --all-extras
```

## Configuration

Copy and edit `forge.yaml` to configure models and quality thresholds:

```yaml
models:
  supervisor: "claude-sonnet-4-20250514"
  coder: "claude-sonnet-4-20250514"
  # ...

quality_thresholds:
  idea_refinement: 0.7
  implementation: 0.8
  # ...
```

## Usage

### Full pipeline (idea to shipped product)

```bash
forge run "build a CLI tool that converts markdown to PDF"
```

### Stepped workflow (pause, inspect, and refine between stages)

```bash
# Stage 1: Idea → Spec
forge ideate "build a CLI tool that converts markdown to PDF"
# → my-tool.spec.json

# Stage 2: Spec → PRD + SDD
forge plan my-tool.spec.json
# → my-tool.plan.json

# Stage 3: Plan → HLD + Components
forge design my-tool.plan.json
# → my-tool.design.json

# Stages 4-6: Design → Code → Test → Ship
forge build my-tool.design.json -o ./my-tool
```

`forge build` auto-detects which stage to start from based on the JSON file contents, so you can also skip intermediate steps:

```bash
forge build my-tool.spec.json    # runs stages 2-6
forge build my-tool.plan.json    # runs stages 3-6
forge build my-tool.design.json  # runs stages 4-6
```

### Common options

```
-c, --config PATH    Path to forge.yaml
-o, --output PATH    Output path/directory
-v, --verbose        Show detailed output
--skip-gates         Skip supervisor quality gates
--dry-run            Skip GitHub and publishing
--no-github          Skip GitHub repo creation
--no-publish         Skip package publishing
```

## Development

```bash
uv sync --all-extras
uv run pytest tests/ -v
```
