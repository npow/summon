"""Click CLI: forge run / ideate / build subcommands."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from forge.config import ForgeConfig
from forge.pipeline import build_pipeline

console = Console()

STAGE_INFO = [
    ("idea_refinement", "Idea Refinement", "Analyzing ambiguities, resolving them, writing spec"),
    ("product_planning", "Product Planning", "Writing PRD, SDD, critic review"),
    ("design", "High-Level Design", "Architecting components, splitting for parallel build"),
    ("implementation", "Implementation", "LLD → Code → Review per component"),
    ("integration_testing", "Testing", "Integration, test writing, running tests, bug fixing"),
    ("release", "Package & Release", "Packaging, docs, GitHub setup"),
]


def _make_stage_table(
    current_stage: str,
    gate_scores: dict[str, float],
    elapsed: dict[str, float],
    from_stage: int = 1,
    until_stage: int = 6,
) -> Table:
    """Build a live-updating stage progress table."""
    table = Table(title="Pipeline Progress", show_header=True, header_style="bold", expand=True)
    table.add_column("#", width=3, justify="center")
    table.add_column("Stage", min_width=20)
    table.add_column("Status", width=12, justify="center")
    table.add_column("Gate", width=10, justify="center")
    table.add_column("Time", width=8, justify="right")

    hit_current = False
    for i, (key, label, _desc) in enumerate(STAGE_INFO, 1):
        if i < from_stage or i > until_stage:
            continue

        score = gate_scores.get(key)
        t = elapsed.get(key)
        time_str = f"{t:.1f}s" if t is not None else ""

        if key == current_stage:
            status = "[bold yellow]● Running[/bold yellow]"
            hit_current = True
        elif not hit_current:
            if score is not None:
                status = "[green]✓ Done[/green]"
            else:
                status = "[green]✓ Done[/green]"
        else:
            status = "[dim]○ Pending[/dim]"

        gate_str = ""
        if score is not None:
            if score >= 0.8:
                gate_str = f"[green]{score:.2f}[/green]"
            elif score >= 0.6:
                gate_str = f"[yellow]{score:.2f}[/yellow]"
            else:
                gate_str = f"[red]{score:.2f}[/red]"

        table.add_row(str(i), label, status, gate_str, time_str)

    return table


def _run_pipeline(
    pipeline,
    initial_state: dict,
    *,
    verbose: bool = False,
    from_stage: int = 1,
    until_stage: int = 6,
) -> dict:
    """Stream a pipeline and display live progress. Returns the accumulated final state."""
    current_stage = ""
    gate_scores: dict[str, float] = {}
    stage_start_times: dict[str, float] = {}
    stage_elapsed: dict[str, float] = {}
    final_state: dict = {}
    pipeline_start = time.time()

    with Live(
        _make_stage_table("", gate_scores, stage_elapsed, from_stage, until_stage),
        console=console,
        refresh_per_second=4,
    ) as live:
        for event in pipeline.stream(initial_state, stream_mode="updates"):
            for node_name, update in event.items():
                if not isinstance(update, dict):
                    continue

                # Track current stage
                new_stage = update.get("current_stage")
                if new_stage and new_stage != current_stage:
                    if current_stage and current_stage in stage_start_times:
                        stage_elapsed[current_stage] = time.time() - stage_start_times[current_stage]
                    current_stage = new_stage
                    stage_start_times[current_stage] = time.time()
                    live.update(_make_stage_table(current_stage, gate_scores, stage_elapsed, from_stage, until_stage))

                # Track gate results
                gate_results = update.get("gate_results")
                if gate_results:
                    for gr in gate_results:
                        stage_name = gr.get("stage", "")
                        gate_scores[stage_name] = gr.get("score", 0)
                        if not gr.get("passed"):
                            retry_num = update.get("stage_retries", {}).get(stage_name, 0)
                            live.console.print(
                                f"  [yellow]Gate retry {retry_num}: {gr.get('feedback', '')[:120]}[/yellow]"
                            )
                    live.update(_make_stage_table(current_stage, gate_scores, stage_elapsed, from_stage, until_stage))

                # Verbose node output
                if verbose:
                    keys = [k for k in update.keys() if not k.startswith("_")]
                    if keys:
                        live.console.print(f"  [dim]{node_name} → {', '.join(keys)}[/dim]")

                # Accumulate final state
                final_state.update(update)

        # Record final stage time
        if current_stage and current_stage in stage_start_times:
            stage_elapsed[current_stage] = time.time() - stage_start_times[current_stage]

    final_state["_total_time"] = time.time() - pipeline_start
    return final_state


def _print_results(final_state: dict, verbose: bool = False):
    """Print the final results panel after a full pipeline run."""
    total_time = final_state.get("_total_time", 0)
    spec = final_state.get("spec", {})
    workspace = final_state.get("workspace_path", "")
    release = final_state.get("release_info", {})

    lines = []
    if spec:
        lines.append(f"[bold]Project:[/bold]     {spec.get('project_name', 'unknown')}")
        lines.append(f"[bold]Description:[/bold] {spec.get('one_liner', 'N/A')}")
        lines.append(f"[bold]Language:[/bold]    {spec.get('language', 'N/A')}")
        lines.append(f"[bold]Type:[/bold]        {spec.get('package_type', 'N/A')}")
    if workspace:
        lines.append(f"[bold]Workspace:[/bold]   {workspace}")

        from forge.workspace import Workspace
        ws = Workspace(workspace)
        files = ws.list_files()
        if files:
            lines.append(f"[bold]Files:[/bold]       {len(files)} files generated")
            for f in sorted(files)[:15]:
                lines.append(f"               {f}")
            if len(files) > 15:
                lines.append(f"               ... and {len(files) - 15} more")

    if release:
        if release.get("github_repo_url"):
            lines.append(f"[bold]GitHub:[/bold]      {release['github_repo_url']}")
        if release.get("published_url"):
            lines.append(f"[bold]Published:[/bold]   {release['published_url']}")

    lines.append(f"\n[dim]Total time: {total_time:.1f}s[/dim]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold green]✓ Pipeline Complete[/bold green]",
        padding=(1, 2),
    ))

    if verbose and spec:
        console.print("\n[bold]Full Spec:[/bold]")
        console.print_json(json.dumps(spec, indent=2))


@click.group()
def main():
    """Forge: Autonomous idea-to-product pipeline."""
    pass


@main.command()
@click.argument("idea")
@click.option("--config", "-c", "config_path", default=None, help="Path to forge.yaml")
@click.option("--output", "-o", "output_dir", default=None, help="Output directory for generated project")
@click.option("--skip-gates", is_flag=True, help="Skip supervisor quality gates")
@click.option("--no-github", is_flag=True, help="Skip GitHub repo creation")
@click.option("--no-publish", is_flag=True, help="Skip package publishing")
@click.option("--dry-run", is_flag=True, help="Run pipeline but don't create external resources")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def run(
    idea: str,
    config_path: str | None,
    output_dir: str | None,
    skip_gates: bool,
    no_github: bool,
    no_publish: bool,
    dry_run: bool,
    verbose: bool,
):
    """Run the full pipeline: idea → spec → design → code → test → ship.

    Example: forge run "build a CLI tool that converts markdown to PDF"
    """
    console.print()
    console.print(Panel(
        f"[bold]{idea}[/bold]",
        title="[bold blue]⚒ Forge Pipeline[/bold blue]",
        subtitle="[dim]idea → spec → design → code → test → ship[/dim]",
        padding=(1, 2),
    ))

    config = ForgeConfig.load(config_path)

    if dry_run:
        no_github = True
        no_publish = True
        console.print("[dim]  --dry-run: skipping GitHub and publishing[/dim]")

    if skip_gates:
        console.print("[dim]  --skip-gates: quality gates disabled[/dim]")

    pipeline = build_pipeline(
        config=config,
        skip_gates=skip_gates,
        skip_github=no_github,
        skip_publish=no_publish,
    )

    initial_state = {"raw_idea": idea}
    if output_dir:
        initial_state["workspace_path"] = str(Path(output_dir).resolve())

    console.print()

    try:
        final_state = _run_pipeline(pipeline, initial_state, verbose=verbose)
        console.print()
        _print_results(final_state, verbose=verbose)

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user (Ctrl+C)[/yellow]")
        sys.exit(1)
    except EnvironmentError as e:
        console.print(f"\n[red bold]Configuration Error[/red bold]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        console.print(f"\n[red bold]Pipeline Failed[/red bold]")
        console.print(f"[red]{error_msg}[/red]")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        else:
            console.print("[dim]Run with -v for full traceback[/dim]")
        sys.exit(1)


@main.command()
@click.argument("idea")
@click.option("--config", "-c", "config_path", default=None, help="Path to forge.yaml")
@click.option("--output", "-o", "output_path", default=None, help="Output path for spec JSON file")
@click.option("--skip-gates", is_flag=True, help="Skip supervisor quality gates")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def ideate(
    idea: str,
    config_path: str | None,
    output_path: str | None,
    skip_gates: bool,
    verbose: bool,
):
    """Run Stage 1 only: refine an idea into a spec JSON file.

    Example: forge ideate "build a CLI tool that converts markdown to PDF"
    """
    console.print()
    console.print(Panel(
        f"[bold]{idea}[/bold]",
        title="[bold blue]⚒ Forge Ideate[/bold blue]",
        subtitle="[dim]idea → spec[/dim]",
        padding=(1, 2),
    ))

    config = ForgeConfig.load(config_path)

    if skip_gates:
        console.print("[dim]  --skip-gates: quality gates disabled[/dim]")

    pipeline = build_pipeline(
        config=config,
        skip_gates=skip_gates,
        until_stage=1,
    )

    initial_state = {"raw_idea": idea}
    console.print()

    try:
        final_state = _run_pipeline(pipeline, initial_state, verbose=verbose, until_stage=1)
        console.print()

        spec = final_state.get("spec", {})
        if not spec:
            console.print("[red]No spec was produced by Stage 1.[/red]")
            sys.exit(1)

        # Determine output file path
        project_name = spec.get("project_name", "forge-project")
        if output_path is None:
            output_path = f"{project_name}.spec.json"

        # Save spec to file
        spec_path = Path(output_path)
        spec_path.write_text(json.dumps(spec, indent=2) + "\n")

        total_time = final_state.get("_total_time", 0)
        console.print(Panel(
            f"[bold]Project:[/bold]  {spec.get('project_name', 'unknown')}\n"
            f"[bold]One-liner:[/bold] {spec.get('one_liner', 'N/A')}\n"
            f"[bold]Saved to:[/bold] {spec_path}\n"
            f"\n[dim]Total time: {total_time:.1f}s[/dim]",
            title="[bold green]✓ Spec Ready[/bold green]",
            padding=(1, 2),
        ))

        # Print the full spec JSON
        console.print("\n[bold]Spec:[/bold]")
        console.print_json(json.dumps(spec, indent=2))

        console.print(f"\n[dim]Next: forge plan {spec_path}[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user (Ctrl+C)[/yellow]")
        sys.exit(1)
    except EnvironmentError as e:
        console.print(f"\n[red bold]Configuration Error[/red bold]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        console.print(f"\n[red bold]Ideation Failed[/red bold]")
        console.print(f"[red]{error_msg}[/red]")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        else:
            console.print("[dim]Run with -v for full traceback[/dim]")
        sys.exit(1)


def _load_json_file(file_path: str) -> dict:
    """Load and return a JSON file, exiting on error."""
    path = Path(file_path)
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[red bold]Failed to load JSON file[/red bold]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


def _detect_stage_and_state(data: dict) -> tuple[int, dict]:
    """Auto-detect which stage to start from based on JSON keys.

    Returns (from_stage, initial_state) where initial_state has all
    known keys injected for the pipeline.
    """
    # If the JSON has 'components' or 'hld', design is done → start at stage 4
    if "components" in data or "hld" in data:
        return 4, {
            "spec": data.get("spec", {}),
            "prd": data.get("prd", {}),
            "sdd": data.get("sdd", {}),
            "hld": data.get("hld", {}),
            "components": data.get("components", []),
        }

    # If it has 'prd' or 'sdd', planning is done → start at stage 3
    if "prd" in data or "sdd" in data:
        return 3, {
            "spec": data.get("spec", {}),
            "prd": data.get("prd", {}),
            "sdd": data.get("sdd", {}),
        }

    # If it has a 'spec' wrapper key → start at stage 2
    if "spec" in data:
        return 2, {"spec": data["spec"]}

    # Bare spec (has 'project_name' at top level) → wrap and start at stage 2
    if "project_name" in data:
        return 2, {"spec": data}

    # Fallback: treat as bare spec
    return 2, {"spec": data}


@main.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--config", "-c", "config_path", default=None, help="Path to forge.yaml")
@click.option("--output", "-o", "output_path", default=None, help="Output path for plan JSON file")
@click.option("--skip-gates", is_flag=True, help="Skip supervisor quality gates")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def plan(
    spec_file: str,
    config_path: str | None,
    output_path: str | None,
    skip_gates: bool,
    verbose: bool,
):
    """Run Stage 2 only: generate PRD + SDD from a spec JSON file.

    Example: forge plan my-tool.spec.json
    """
    data = _load_json_file(spec_file)

    # Accept bare spec or wrapped {"spec": ...}
    if "spec" in data:
        spec = data["spec"]
    else:
        spec = data

    project_name = spec.get("project_name", "unknown")

    console.print()
    console.print(Panel(
        f"[bold]Project:[/bold] {project_name}\n"
        f"[bold]Spec:[/bold]    {spec_file}",
        title="[bold blue]⚒ Forge Plan[/bold blue]",
        subtitle="[dim]spec → PRD + SDD[/dim]",
        padding=(1, 2),
    ))

    config = ForgeConfig.load(config_path)

    if skip_gates:
        console.print("[dim]  --skip-gates: quality gates disabled[/dim]")

    pipeline = build_pipeline(
        config=config,
        skip_gates=skip_gates,
        from_stage=2,
        until_stage=2,
    )

    initial_state = {"spec": spec}
    console.print()

    try:
        final_state = _run_pipeline(
            pipeline, initial_state, verbose=verbose, from_stage=2, until_stage=2,
        )
        console.print()

        prd = final_state.get("prd", {})
        sdd = final_state.get("sdd", {})
        if not prd and not sdd:
            console.print("[red]No PRD/SDD was produced by Stage 2.[/red]")
            sys.exit(1)

        # Determine output file path
        if output_path is None:
            output_path = f"{project_name}.plan.json"

        # Save plan to file
        plan_data = {"spec": spec, "prd": prd, "sdd": sdd}
        plan_path = Path(output_path)
        plan_path.write_text(json.dumps(plan_data, indent=2) + "\n")

        total_time = final_state.get("_total_time", 0)
        console.print(Panel(
            f"[bold]Project:[/bold]  {project_name}\n"
            f"[bold]Saved to:[/bold] {plan_path}\n"
            f"\n[dim]Total time: {total_time:.1f}s[/dim]",
            title="[bold green]✓ Plan Ready[/bold green]",
            padding=(1, 2),
        ))

        console.print(f"\n[dim]Next: forge design {plan_path}[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user (Ctrl+C)[/yellow]")
        sys.exit(1)
    except EnvironmentError as e:
        console.print(f"\n[red bold]Configuration Error[/red bold]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        console.print(f"\n[red bold]Planning Failed[/red bold]")
        console.print(f"[red]{error_msg}[/red]")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        else:
            console.print("[dim]Run with -v for full traceback[/dim]")
        sys.exit(1)


@main.command()
@click.argument("plan_file", type=click.Path(exists=True))
@click.option("--config", "-c", "config_path", default=None, help="Path to forge.yaml")
@click.option("--output", "-o", "output_path", default=None, help="Output path for design JSON file")
@click.option("--skip-gates", is_flag=True, help="Skip supervisor quality gates")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def design(
    plan_file: str,
    config_path: str | None,
    output_path: str | None,
    skip_gates: bool,
    verbose: bool,
):
    """Run Stage 3 only: generate HLD + components from a plan JSON file.

    Example: forge design my-tool.plan.json
    """
    data = _load_json_file(plan_file)

    spec = data.get("spec", {})
    prd = data.get("prd", {})
    sdd = data.get("sdd", {})
    project_name = spec.get("project_name", "unknown")

    if not prd and not sdd:
        console.print("[red bold]Plan file must contain 'prd' and/or 'sdd' keys.[/red bold]")
        sys.exit(1)

    console.print()
    console.print(Panel(
        f"[bold]Project:[/bold] {project_name}\n"
        f"[bold]Plan:[/bold]    {plan_file}",
        title="[bold blue]⚒ Forge Design[/bold blue]",
        subtitle="[dim]PRD + SDD → HLD + components[/dim]",
        padding=(1, 2),
    ))

    config = ForgeConfig.load(config_path)

    if skip_gates:
        console.print("[dim]  --skip-gates: quality gates disabled[/dim]")

    pipeline = build_pipeline(
        config=config,
        skip_gates=skip_gates,
        from_stage=3,
        until_stage=3,
    )

    initial_state = {"spec": spec, "prd": prd, "sdd": sdd}
    console.print()

    try:
        final_state = _run_pipeline(
            pipeline, initial_state, verbose=verbose, from_stage=3, until_stage=3,
        )
        console.print()

        hld = final_state.get("hld", {})
        components = final_state.get("components", [])
        if not hld and not components:
            console.print("[red]No HLD/components were produced by Stage 3.[/red]")
            sys.exit(1)

        # Determine output file path
        if output_path is None:
            output_path = f"{project_name}.design.json"

        # Save design to file
        design_data = {
            "spec": spec,
            "prd": prd,
            "sdd": sdd,
            "hld": hld,
            "components": components,
        }
        design_path = Path(output_path)
        design_path.write_text(json.dumps(design_data, indent=2) + "\n")

        total_time = final_state.get("_total_time", 0)
        console.print(Panel(
            f"[bold]Project:[/bold]  {project_name}\n"
            f"[bold]Saved to:[/bold] {design_path}\n"
            f"\n[dim]Total time: {total_time:.1f}s[/dim]",
            title="[bold green]✓ Design Ready[/bold green]",
            padding=(1, 2),
        ))

        console.print(f"\n[dim]Next: forge build {design_path}[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user (Ctrl+C)[/yellow]")
        sys.exit(1)
    except EnvironmentError as e:
        console.print(f"\n[red bold]Configuration Error[/red bold]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        console.print(f"\n[red bold]Design Failed[/red bold]")
        console.print(f"[red]{error_msg}[/red]")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        else:
            console.print("[dim]Run with -v for full traceback[/dim]")
        sys.exit(1)


@main.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--config", "-c", "config_path", default=None, help="Path to forge.yaml")
@click.option("--output", "-o", "output_dir", default=None, help="Output directory for generated project")
@click.option("--skip-gates", is_flag=True, help="Skip supervisor quality gates")
@click.option("--no-github", is_flag=True, help="Skip GitHub repo creation")
@click.option("--no-publish", is_flag=True, help="Skip package publishing")
@click.option("--dry-run", is_flag=True, help="Run pipeline but don't create external resources")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def build(
    spec_file: str,
    config_path: str | None,
    output_dir: str | None,
    skip_gates: bool,
    no_github: bool,
    no_publish: bool,
    dry_run: bool,
    verbose: bool,
):
    """Build a project from a JSON file (auto-detects start stage).

    Accepts spec.json (stages 2-6), plan.json (stages 3-6), or design.json (stages 4-6).

    Example: forge build my-tool.design.json -o /tmp/my-tool
    """
    data = _load_json_file(spec_file)
    from_stage, initial_state = _detect_stage_and_state(data)

    spec = initial_state.get("spec", {})
    project_name = spec.get("project_name", "unknown")

    stage_labels = {2: "spec", 3: "plan", 4: "design"}
    start_label = stage_labels.get(from_stage, "spec")

    console.print()
    console.print(Panel(
        f"[bold]Project:[/bold] {project_name}\n"
        f"[bold]Input:[/bold]   {spec_file}\n"
        f"[bold]Start:[/bold]   stage {from_stage} ({start_label} detected)",
        title="[bold blue]⚒ Forge Build[/bold blue]",
        subtitle=f"[dim]{start_label} → code → test → ship[/dim]",
        padding=(1, 2),
    ))

    config = ForgeConfig.load(config_path)

    if dry_run:
        no_github = True
        no_publish = True
        console.print("[dim]  --dry-run: skipping GitHub and publishing[/dim]")

    if skip_gates:
        console.print("[dim]  --skip-gates: quality gates disabled[/dim]")

    pipeline = build_pipeline(
        config=config,
        skip_gates=skip_gates,
        skip_github=no_github,
        skip_publish=no_publish,
        from_stage=from_stage,
    )

    if output_dir:
        initial_state["workspace_path"] = str(Path(output_dir).resolve())

    console.print()

    try:
        final_state = _run_pipeline(
            pipeline, initial_state, verbose=verbose, from_stage=from_stage,
        )
        # Ensure spec is in final_state for _print_results
        final_state.setdefault("spec", spec)
        console.print()
        _print_results(final_state, verbose=verbose)

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user (Ctrl+C)[/yellow]")
        sys.exit(1)
    except EnvironmentError as e:
        console.print(f"\n[red bold]Configuration Error[/red bold]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        console.print(f"\n[red bold]Build Failed[/red bold]")
        console.print(f"[red]{error_msg}[/red]")
        if verbose:
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        else:
            console.print("[dim]Run with -v for full traceback[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
