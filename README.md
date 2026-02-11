# Oneshot

**Describe your idea. Get a working project.**

Oneshot takes a plain-English description and builds you a complete, working codebase — with tests, docs, and packaging — in one command.

```bash
oneshot run "youtube transcriber that takes a URL and returns the transcript as text"
```

What comes out: a real project with source files, requirements, unit tests, acceptance tests, and a working entry point. Not scaffolding. Not boilerplate. Actual implementations that run.

## Quickstart

```bash
# Install
git clone https://github.com/yourname/oneshot && cd oneshot
uv sync --all-extras

# Set your API key
export ANTHROPIC_API_KEY=sk-...

# Build something
oneshot run "CLI tool that converts markdown to PDF" -o ./md2pdf
```

That's it. Go make coffee. Come back to a working project in `./md2pdf`.

## What it actually does

Your one-liner goes through a full software development lifecycle — automatically:

1. **Refines** your idea into a precise spec (resolves ambiguities, fills gaps)
2. **Plans** the architecture (PRD, system design, component breakdown)
3. **Implements** each component in parallel (with code review)
4. **Integrates** everything into a cohesive project
5. **Tests** it (import validation, unit tests, acceptance tests — with fix loops)
6. **Packages** it (README, setup files, docs)

If something breaks, it fixes it. If code comes out degenerate (repetitive, truncated, stub-only), it detects that and regenerates from scratch.

## Stepped workflow

Don't want to run everything at once? Break it up:

```bash
oneshot ideate "your idea"              # idea -> spec.json
oneshot plan my-tool.spec.json          # spec -> plan.json
oneshot design my-tool.plan.json        # plan -> design.json
oneshot build my-tool.design.json -o .  # design -> working project
```

Inspect and edit the JSON between steps. `oneshot build` auto-detects where to pick up.

## Configuration

Works with Claude (default) or OpenAI models. Edit `oneshot.yaml`:

```yaml
models:
  supervisor: "claude-sonnet-4-20250514"   # or "gpt-4o"
  coder: "claude-sonnet-4-20250514"
  test_writer: "gpt-4o-mini"              # cheaper models for simpler tasks
```

Use `oneshot-openai.yaml` for a full OpenAI configuration:

```bash
oneshot run "your idea" -c oneshot-openai.yaml
```

## Options

```
-c, --config PATH    Config file (default: oneshot.yaml)
-o, --output PATH    Output directory
-v, --verbose        Show what's happening
--skip-gates         Skip quality gates
--dry-run            Skip GitHub/publishing
```

## Requirements

- Python 3.11+
- An API key for [Anthropic](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/)
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Contributing

Contributions are welcome. Open an issue first for anything non-trivial.

```bash
git clone https://github.com/yourname/oneshot && cd oneshot
uv sync --all-extras
uv run pytest tests/ -v
```

## License

[MIT](LICENSE)
