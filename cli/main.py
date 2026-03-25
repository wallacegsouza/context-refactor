"""CLI entry point for ContextRefactor.

Usage::

    # Full analysis (default)
    context-refactor analyze /path/to/project

    # Only check budget
    context-refactor budget /path/to/project --context-size 200000

    # Detect candidates
    context-refactor candidates /path/to/project

    # Generate plan
    context-refactor plan /path/to/project --safety-margin 0.75

    # Start MCP server
    context-refactor serve
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError as err:
    sys.stderr.write(
        "typer and rich are required for the CLI. Install with:\n"
        "  pip install typer[all]\n"
    )
    raise SystemExit(1) from err

app = typer.Typer(
    name="context-refactor",
    help="Analyse & refactor a codebase to fit inside an LLM context window.",
    add_completion=False,
)
console = Console()

# ── Shared helpers ────────────────────────────────────────────────────────────


def _resolve_path(project_path: str) -> str:
    p = Path(project_path).resolve()
    if not p.is_dir():
        console.print(f"[red]Error:[/] {p} is not a directory.")
        raise typer.Exit(1)
    return str(p)


def _print_json(data: dict) -> None:
    console.print_json(json.dumps(data, indent=2, ensure_ascii=False))


def _human(n: int) -> str:
    return f"{n:,}"


def _csv_to_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _analysis_options(
    profile: str,
    config_path: str | None,
    exclude_dirs: str | None,
    exclude_globs: str | None,
    exclude_files: str | None,
    include_categories: str | None,
    exclude_categories: str | None,
) -> dict[str, object]:
    return {
        "analysis_profile": profile,
        "config_path": config_path,
        "exclude_dirs": _csv_to_list(exclude_dirs),
        "exclude_globs": _csv_to_list(exclude_globs),
        "exclude_files": _csv_to_list(exclude_files),
        "include_categories": _csv_to_list(include_categories),
        "exclude_categories": _csv_to_list(exclude_categories),
    }


def _print_analysis_scope(result: dict) -> None:
    scope = result.get("analysis_scope") or {}
    if not scope:
        return

    include_categories = ", ".join(scope.get("include_categories") or []) or "all"
    exclude_categories = ", ".join(scope.get("exclude_categories") or []) or "none"
    exclude_dirs = ", ".join(scope.get("exclude_dirs") or []) or "none"
    exclude_globs = ", ".join(scope.get("exclude_globs") or []) or "none"
    exclude_files = ", ".join(scope.get("exclude_files") or []) or "none"
    category_counts = result.get("category_counts") or {}
    category_tokens = result.get("category_tokens") or {}
    noise_summary = result.get("noise_summary") or {}
    signal_score = result.get("signal_score") or {}
    category_lines = []
    for category in sorted(category_counts):
        category_lines.append(
            f"{category}: {_human(category_counts[category])} files / {_human(category_tokens.get(category, 0))} tokens"
        )

    body = (
        f"[bold]Profile:[/] {scope.get('profile', 'default')}\n"
        f"[bold]Config:[/] {scope.get('config_path') or 'none'}\n"
        f"[bold]Include categories:[/] {include_categories}\n"
        f"[bold]Exclude categories:[/] {exclude_categories}\n"
        f"[bold]Exclude dirs:[/] {exclude_dirs}\n"
        f"[bold]Exclude globs:[/] {exclude_globs}\n"
        f"[bold]Exclude files:[/] {exclude_files}"
    )
    if category_lines:
        body += "\n[bold]Category mix:[/] " + " | ".join(category_lines)

    if noise_summary:
        body += (
            "\n[bold]Noise summary:[/] "
            f"scanner={_human(noise_summary.get('scanner_files', 0))} files / {_human(noise_summary.get('scanner_tokens', 0))} tokens"
            f" -> after filters={_human(noise_summary.get('files_after_filters', 0))} files / {_human(noise_summary.get('tokens_after_filters', 0))} tokens"
            f" | filtered_by_category={_human(noise_summary.get('filtered_by_category_files', 0))} files"
            f" ({noise_summary.get('file_reduction_ratio', 0.0):.1%})"
        )

    if signal_score:
        body += (
            "\n[bold]Signal score:[/] "
            f"{signal_score.get('value', 0)} / 100"
            f" | noise_ratio={signal_score.get('noise_ratio', 0.0):.1%}"
            f" | method={signal_score.get('method', '-') }"
        )

    console.print(Panel(body, title="Analysis Scope", border_style="blue"))


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def analyze(
    project_path: str = typer.Argument(..., help="Path to the project root."),
    context_size: int = typer.Option(128_000, "--context-size", "-c", help="LLM context window size."),
    safety_margin: float = typer.Option(0.80, "--safety-margin", "-s", help="Usable fraction (0-1)."),
    estimator: str = typer.Option("bytes", "--estimator", "-e", help="bytes|chars|whitespace|heuristic"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON instead of tables."),
    top_n: int = typer.Option(50, "--top", "-n", help="Top N files to display."),
    profile: str = typer.Option("default", "--profile", help="Analysis profile: default|full|source-only|docs"),
    config_path: str | None = typer.Option(None, "--config", help="Path to a .context-refactor.json file."),
    exclude_dirs: str | None = typer.Option(None, "--exclude-dirs", help="Comma-separated directory names or relative paths to exclude."),
    exclude_globs: str | None = typer.Option(None, "--exclude-globs", help="Comma-separated glob patterns to exclude."),
    exclude_files: str | None = typer.Option(None, "--exclude-files", help="Comma-separated file patterns to exclude."),
    include_categories: str | None = typer.Option(None, "--include-categories", help="Comma-separated categories to include."),
    exclude_categories: str | None = typer.Option(None, "--exclude-categories", help="Comma-separated categories to exclude."),
) -> None:
    """Full project analysis with recommendations and refactoring plan."""
    from mcp_server.tools import analyze_project

    path = _resolve_path(project_path)
    result = analyze_project(
        project_path=path,
        llm_context_size=context_size,
        safety_margin=safety_margin,
        estimator=estimator,
        top_n=top_n,
        **_analysis_options(
            profile=profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
    )

    if output_json:
        _print_json(result)
        return

    summary = result["project_summary"]
    budget = result["context_budget"]
    _print_analysis_scope(result)

    # ── Summary panel
    fits = "[green]YES[/]" if summary["fits_context"] else "[red]NO[/]"
    console.print(Panel(
        f"[bold]Files:[/] {_human(summary['files'])}   "
        f"[bold]Tokens:[/] {_human(summary['total_tokens'])}   "
        f"[bold]Budget:[/] {_human(summary['context_budget'])}   "
        f"[bold]Fits:[/] {fits}   "
        f"[bold]Overflow:[/] {_human(budget['overflow_tokens'])} "
        f"({budget['overflow_ratio']:.1%})",
        title="Project Summary",
        border_style="cyan",
    ))

    # ── Largest files table
    table = Table(title="Largest Files by Tokens", show_lines=False)
    table.add_column("File", style="cyan", no_wrap=True, max_width=70)
    table.add_column("Category", style="magenta")
    table.add_column("Tokens", justify="right", style="yellow")
    for f in result["largest_files"][:20]:
        table.add_row(f["path"], f["category"], _human(f["tokens"]))
    console.print(table)

    # ── Recommendations
    recs = result["refactor_recommendations"]
    if recs:
        rec_table = Table(title=f"Refactor Recommendations ({len(recs)} found)", show_lines=True)
        rec_table.add_column("#", justify="right", width=4)
        rec_table.add_column("Priority", width=10)
        rec_table.add_column("Technique", width=22)
        rec_table.add_column("File", max_width=50)
        rec_table.add_column("Description", max_width=60)
        for i, r in enumerate(recs[:25], 1):
            prio_color = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "dim"}.get(r["priority"], "")
            rec_table.add_row(
                str(i),
                f"[{prio_color}]{r['priority']}[/]",
                r["technique"],
                r["file_path"],
                r["description"][:80],
            )
        console.print(rec_table)

    # ── Plan
    plan = result.get("refactor_plan")
    if plan and plan.get("steps"):
        console.print(Panel(
            f"[bold]Steps:[/] {len(plan['steps'])}   "
            f"[bold]Est. reduction:[/] {_human(plan['total_estimated_token_reduction'])} tokens   "
            f"[bold]Projected after:[/] {_human(plan['projected_tokens_after'])} tokens   "
            f"[bold]Fits after:[/] {'[green]YES[/]' if plan['fits_context_after'] else '[red]NO[/]'}",
            title="Refactoring Plan",
            border_style="green",
        ))
        for step in plan["steps"]:
            console.print(
                f"\n  [bold cyan]Step {step['step_number']}:[/] {step['title']}\n"
                f"  Techniques: {', '.join(step['techniques'])}\n"
                f"  Files affected: {len(step['affected_files'])}"
            )


@app.command()
def budget(
    project_path: str = typer.Argument(..., help="Path to the project root."),
    context_size: int = typer.Option(128_000, "--context-size", "-c"),
    safety_margin: float = typer.Option(0.80, "--safety-margin", "-s"),
    estimator: str = typer.Option("bytes", "--estimator", "-e"),
    output_json: bool = typer.Option(False, "--json"),
    profile: str = typer.Option("default", "--profile", help="Analysis profile: default|full|source-only|docs"),
    config_path: str | None = typer.Option(None, "--config", help="Path to a .context-refactor.json file."),
    exclude_dirs: str | None = typer.Option(None, "--exclude-dirs", help="Comma-separated directory names or relative paths to exclude."),
    exclude_globs: str | None = typer.Option(None, "--exclude-globs", help="Comma-separated glob patterns to exclude."),
    exclude_files: str | None = typer.Option(None, "--exclude-files", help="Comma-separated file patterns to exclude."),
    include_categories: str | None = typer.Option(None, "--include-categories", help="Comma-separated categories to include."),
    exclude_categories: str | None = typer.Option(None, "--exclude-categories", help="Comma-separated categories to exclude."),
) -> None:
    """Check if the project fits inside an LLM context window."""
    from mcp_server.tools import context_budget

    path = _resolve_path(project_path)
    result = context_budget(
        project_path=path,
        llm_context_size=context_size,
        safety_margin=safety_margin,
        estimator=estimator,
        **_analysis_options(
            profile=profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
    )

    if output_json:
        _print_json(result)
        return

    _print_analysis_scope(result)
    fits = "[green]YES[/]" if result["fits_context"] else "[red]NO[/]"
    console.print(Panel(
        f"[bold]Context size:[/] {_human(result['llm_context_size'])}   "
        f"[bold]Safety margin:[/] {result['safety_margin']:.0%}\n"
        f"[bold]Budget:[/] {_human(result['context_budget'])}   "
        f"[bold]Total tokens:[/] {_human(result['total_tokens'])}   "
        f"[bold]Files:[/] {_human(result['total_files'])}\n"
        f"[bold]Fits:[/] {fits}   "
        f"[bold]Overflow:[/] {_human(result['overflow_tokens'])} "
        f"({result['overflow_ratio']:.1%})",
        title="Context Budget",
        border_style="cyan",
    ))


@app.command()
def candidates(
    project_path: str = typer.Argument(..., help="Path to the project root."),
    estimator: str = typer.Option("bytes", "--estimator", "-e"),
    top_n: int = typer.Option(50, "--top", "-n"),
    output_json: bool = typer.Option(False, "--json"),
    profile: str = typer.Option("default", "--profile", help="Analysis profile: default|full|source-only|docs"),
    config_path: str | None = typer.Option(None, "--config", help="Path to a .context-refactor.json file."),
    exclude_dirs: str | None = typer.Option(None, "--exclude-dirs", help="Comma-separated directory names or relative paths to exclude."),
    exclude_globs: str | None = typer.Option(None, "--exclude-globs", help="Comma-separated glob patterns to exclude."),
    exclude_files: str | None = typer.Option(None, "--exclude-files", help="Comma-separated file patterns to exclude."),
    include_categories: str | None = typer.Option(None, "--include-categories", help="Comma-separated categories to include."),
    exclude_categories: str | None = typer.Option(None, "--exclude-categories", help="Comma-separated categories to exclude."),
) -> None:
    """Detect code smells and refactoring candidates."""
    from mcp_server.tools import detect_refactor_candidates_tool

    path = _resolve_path(project_path)
    result = detect_refactor_candidates_tool(
        project_path=path,
        estimator=estimator,
        top_n=top_n,
        **_analysis_options(
            profile=profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
    )

    if output_json:
        _print_json(result)
        return

    _print_analysis_scope(result)
    console.print(f"\n[bold]Files scanned:[/] {result['total_files_scanned']}")
    console.print(f"[bold]Candidates found:[/] {result['candidates_found']}\n")

    table = Table(title="Refactoring Candidates", show_lines=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("Priority", width=10)
    table.add_column("Smell", width=22)
    table.add_column("Technique", width=22)
    table.add_column("File", max_width=50)
    table.add_column("Reduction", justify="right")

    for i, r in enumerate(result["recommendations"][:top_n], 1):
        prio_color = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "dim"}.get(r["priority"], "")
        table.add_row(
            str(i),
            f"[{prio_color}]{r['priority']}[/]",
            r.get("smell") or "—",
            r["technique"],
            r["file_path"],
            _human(r.get("estimated_token_reduction", 0)),
        )
    console.print(table)


@app.command()
def smells(
    project_path: str = typer.Argument(..., help="Path to the project root."),
    context_size: int = typer.Option(128_000, "--context-size", "-c", help="LLM context window size."),
    estimator: str = typer.Option("bytes", "--estimator", "-e", help="bytes|chars|whitespace|heuristic"),
    top_n: int = typer.Option(50, "--top", "-n", help="Top N files to display."),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON instead of tables."),
    profile: str = typer.Option("default", "--profile", help="Analysis profile: default|full|source-only|docs"),
    config_path: str | None = typer.Option(None, "--config", help="Path to a .context-refactor.json file."),
    exclude_dirs: str | None = typer.Option(None, "--exclude-dirs", help="Comma-separated directory names or relative paths to exclude."),
    exclude_globs: str | None = typer.Option(None, "--exclude-globs", help="Comma-separated glob patterns to exclude."),
    exclude_files: str | None = typer.Option(None, "--exclude-files", help="Comma-separated file patterns to exclude."),
    include_categories: str | None = typer.Option(None, "--include-categories", help="Comma-separated categories to include."),
    exclude_categories: str | None = typer.Option(None, "--exclude-categories", help="Comma-separated categories to exclude."),
) -> None:
    """Detect code smells using the Heuristics Engine (pluggable rules)."""
    from mcp_server.tools import detect_code_smells

    path = _resolve_path(project_path)
    result = detect_code_smells(
        project_path=path,
        llm_context_size=context_size,
        estimator=estimator,
        top_n=top_n,
        **_analysis_options(
            profile=profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
    )

    if output_json:
        _print_json(result)
        return

    _print_analysis_scope(result)
    console.print(f"\n[bold]Files scanned:[/] {_human(result['total_files_scanned'])}")
    console.print(f"[bold]Files with smells:[/] {result['files_with_smells']}\n")

    table = Table(title="Code Smell Results", show_lines=True)
    table.add_column("File", max_width=55, style="cyan")
    table.add_column("Tokens", justify="right", style="yellow")
    table.add_column("Language", width=12, style="magenta")
    table.add_column("Problems", max_width=35)
    table.add_column("Top Suggestions", max_width=45)

    for r in result["results"][:top_n]:
        table.add_row(
            r["file"],
            _human(r["tokens"]),
            r["language"],
            ", ".join(r["problems"][:3]) or "—",
            "; ".join(r["suggested_refactors"][:2]) or "—",
        )
    console.print(table)


@app.command()
def suggest(
    project_path: str = typer.Argument(..., help="Path to the project root."),
    context_size: int = typer.Option(128_000, "--context-size", "-c", help="LLM context window size."),
    safety_margin: float = typer.Option(0.80, "--safety-margin", "-s", help="Usable fraction (0-1)."),
    estimator: str = typer.Option("bytes", "--estimator", "-e", help="bytes|chars|whitespace|heuristic"),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON instead of tables."),
    profile: str = typer.Option("default", "--profile", help="Analysis profile: default|full|source-only|docs"),
    config_path: str | None = typer.Option(None, "--config", help="Path to a .context-refactor.json file."),
    exclude_dirs: str | None = typer.Option(None, "--exclude-dirs", help="Comma-separated directory names or relative paths to exclude."),
    exclude_globs: str | None = typer.Option(None, "--exclude-globs", help="Comma-separated glob patterns to exclude."),
    exclude_files: str | None = typer.Option(None, "--exclude-files", help="Comma-separated file patterns to exclude."),
    include_categories: str | None = typer.Option(None, "--include-categories", help="Comma-separated categories to include."),
    exclude_categories: str | None = typer.Option(None, "--exclude-categories", help="Comma-separated categories to exclude."),
) -> None:
    """Generate refactoring suggestions using the Heuristics Engine."""
    from mcp_server.tools import generate_refactor_suggestions

    path = _resolve_path(project_path)
    result = generate_refactor_suggestions(
        project_path=path,
        llm_context_size=context_size,
        safety_margin=safety_margin,
        estimator=estimator,
        **_analysis_options(
            profile=profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
    )

    if output_json:
        _print_json(result)
        return

    budget_info = result["context_budget"]
    plan_info = result["refactor_plan"]
    _print_analysis_scope(result)

    fits = "[green]YES[/]" if budget_info["fits_context"] else "[red]NO[/]"
    console.print(Panel(
        f"[bold]Tokens:[/] {_human(budget_info['total_tokens'])}   "
        f"[bold]Budget:[/] {_human(budget_info['context_budget'])}   "
        f"[bold]Fits now:[/] {fits}",
        title="Heuristics Engine — Current State",
        border_style="cyan",
    ))

    heuristic_results = result.get("heuristic_results", [])
    if heuristic_results:
        table = Table(title=f"Files with Issues ({len(heuristic_results)} found)", show_lines=False)
        table.add_column("File", max_width=55, style="cyan")
        table.add_column("Tokens", justify="right", style="yellow")
        table.add_column("Problems", max_width=40)
        for r in heuristic_results[:15]:
            table.add_row(
                r["file"],
                _human(r["tokens"]),
                ", ".join(r["problems"][:2]) or "—",
            )
        console.print(table)

    if not plan_info.get("steps"):
        console.print("\n[green]No refactoring needed — project fits the context window.[/]")
        return

    after_fits = "[green]YES[/]" if plan_info["fits_context_after"] else "[red]NO[/]"
    console.print(Panel(
        f"[bold]Steps:[/] {len(plan_info['steps'])}   "
        f"[bold]Est. reduction:[/] {_human(plan_info['total_estimated_token_reduction'])} tokens   "
        f"[bold]Projected after:[/] {_human(plan_info['projected_tokens_after'])} tokens   "
        f"[bold]Fits after:[/] {after_fits}",
        title="Refactoring Plan",
        border_style="green",
    ))

    for step in plan_info["steps"]:
        console.print(f"\n[bold cyan]Step {step['step_number']}. {step['title']}[/]")
        console.print(f"  Techniques: {', '.join(step['techniques'])}")
        console.print(f"  Files: {len(step['affected_files'])}  |  Est. reduction: {_human(step['estimated_token_reduction'])} tokens")
        for line in step["description"].split("\n")[:4]:
            console.print(f"  {line}")


@app.command()
def plan(
    project_path: str = typer.Argument(..., help="Path to the project root."),
    context_size: int = typer.Option(128_000, "--context-size", "-c"),
    safety_margin: float = typer.Option(0.80, "--safety-margin", "-s"),
    estimator: str = typer.Option("bytes", "--estimator", "-e"),
    output_json: bool = typer.Option(False, "--json"),
    profile: str = typer.Option("default", "--profile", help="Analysis profile: default|full|source-only|docs"),
    config_path: str | None = typer.Option(None, "--config", help="Path to a .context-refactor.json file."),
    exclude_dirs: str | None = typer.Option(None, "--exclude-dirs", help="Comma-separated directory names or relative paths to exclude."),
    exclude_globs: str | None = typer.Option(None, "--exclude-globs", help="Comma-separated glob patterns to exclude."),
    exclude_files: str | None = typer.Option(None, "--exclude-files", help="Comma-separated file patterns to exclude."),
    include_categories: str | None = typer.Option(None, "--include-categories", help="Comma-separated categories to include."),
    exclude_categories: str | None = typer.Option(None, "--exclude-categories", help="Comma-separated categories to exclude."),
) -> None:
    """Generate a step-by-step refactoring plan."""
    from mcp_server.tools import generate_refactor_plan_tool

    path = _resolve_path(project_path)
    result = generate_refactor_plan_tool(
        project_path=path,
        llm_context_size=context_size,
        safety_margin=safety_margin,
        estimator=estimator,
        **_analysis_options(
            profile=profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
    )

    if output_json:
        _print_json(result)
        return

    budget_info = result["context_budget"]
    plan_info = result["refactor_plan"]
    _print_analysis_scope(result)

    fits = "[green]YES[/]" if budget_info["fits_context"] else "[red]NO[/]"
    console.print(Panel(
        f"[bold]Tokens:[/] {_human(budget_info['total_tokens'])}   "
        f"[bold]Budget:[/] {_human(budget_info['context_budget'])}   "
        f"[bold]Fits now:[/] {fits}",
        title="Current State",
        border_style="cyan",
    ))

    if not plan_info.get("steps"):
        console.print("\n[green]No refactoring needed — project fits the context window.[/]")
        return

    after_fits = "[green]YES[/]" if plan_info["fits_context_after"] else "[red]NO[/]"
    console.print(Panel(
        f"[bold]Steps:[/] {len(plan_info['steps'])}   "
        f"[bold]Est. reduction:[/] {_human(plan_info['total_estimated_token_reduction'])} tokens   "
        f"[bold]Projected after:[/] {_human(plan_info['projected_tokens_after'])} tokens   "
        f"[bold]Fits after:[/] {after_fits}",
        title="Refactoring Plan",
        border_style="green",
    ))

    for step in plan_info["steps"]:
        console.print(f"\n[bold cyan]Step {step['step_number']}. {step['title']}[/]")
        console.print(f"  Techniques: {', '.join(step['techniques'])}")
        console.print(f"  Files: {len(step['affected_files'])}  |  Est. reduction: {_human(step['estimated_token_reduction'])} tokens")
        for line in step["description"].split("\n")[:5]:
            console.print(f"  {line}")
        if len(step["description"].split("\n")) > 5:
            console.print("  … (truncated)")


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    import asyncio

    from mcp_server.server import run_server

    asyncio.run(run_server())


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    app()


if __name__ == "__main__":
    main()
