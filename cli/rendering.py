"""Shared rendering helpers for CLI output."""

from __future__ import annotations

from typing import Any

from .runtime import Panel, Table, console
from .shared import human


def dependency_enabled(result: dict[str, Any]) -> bool:
    return bool(result.get("dependency_analysis", {}).get("enabled"))


def priority_markup(priority: str) -> str:
    color = {
        "critical": "red",
        "high": "yellow",
        "medium": "cyan",
        "low": "dim",
    }.get(priority, "")
    return f"[{color}]{priority}[/]"


def print_project_summary(summary: dict[str, Any], budget: dict[str, Any]) -> None:
    fits = "[green]YES[/]" if summary["fits_context"] else "[red]NO[/]"
    console.print(
        Panel(
            f"[bold]Files:[/] {human(summary['files'])}   "
            f"[bold]Tokens:[/] {human(summary['total_tokens'])}   "
            f"[bold]Budget:[/] {human(summary['context_budget'])}   "
            f"[bold]Fits:[/] {fits}   "
            f"[bold]Overflow:[/] {human(budget['overflow_tokens'])} "
            f"({budget['overflow_ratio']:.1%})",
            title="Project Summary",
            border_style="cyan",
        )
    )


def print_largest_files(result: dict[str, Any], limit: int = 20) -> None:
    table = Table(title="Largest Files by Tokens", show_lines=False)
    table.add_column("File", style="cyan", no_wrap=True, max_width=70)
    table.add_column("Category", style="magenta")
    table.add_column("Tokens", justify="right", style="yellow")
    if dependency_enabled(result):
        table.add_column("Effective", justify="right", style="green")
    for file_info in result["largest_files"][:limit]:
        row = [file_info["path"], file_info["category"], human(file_info["tokens"])]
        if dependency_enabled(result):
            row.append(human(file_info.get("effective_token_size", file_info["tokens"])))
        table.add_row(*row)
    console.print(table)


def print_refactor_recommendations(recommendations: list[dict[str, Any]], limit: int = 25) -> None:
    if not recommendations:
        return

    table = Table(
        title=f"Refactor Recommendations ({len(recommendations)} found)",
        show_lines=True,
    )
    table.add_column("#", justify="right", width=4)
    table.add_column("Priority", width=10)
    table.add_column("Technique", width=22)
    table.add_column("File", max_width=50)
    table.add_column("Description", max_width=60)
    for index, recommendation in enumerate(recommendations[:limit], 1):
        table.add_row(
            str(index),
            priority_markup(recommendation["priority"]),
            recommendation["technique"],
            recommendation["file_path"],
            recommendation["description"][:80],
        )
    console.print(table)


def print_context_budget(result: dict[str, Any]) -> None:
    fits = "[green]YES[/]" if result["fits_context"] else "[red]NO[/]"
    console.print(
        Panel(
            f"[bold]Context size:[/] {human(result['llm_context_size'])}   "
            f"[bold]Safety margin:[/] {result['safety_margin']:.0%}\n"
            f"[bold]Budget:[/] {human(result['context_budget'])}   "
            f"[bold]Total tokens:[/] {human(result['total_tokens'])}   "
            f"[bold]Files:[/] {human(result['total_files'])}\n"
            f"[bold]Fits:[/] {fits}   "
            f"[bold]Overflow:[/] {human(result['overflow_tokens'])} "
            f"({result['overflow_ratio']:.1%})",
            title="Context Budget",
            border_style="cyan",
        )
    )


def print_refactoring_candidates(result: dict[str, Any], top_n: int) -> None:
    console.print(f"\n[bold]Files scanned:[/] {result['total_files_scanned']}")
    console.print(f"[bold]Candidates found:[/] {result['candidates_found']}\n")

    table = Table(title="Refactoring Candidates", show_lines=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("Priority", width=10)
    table.add_column("Smell", width=22)
    table.add_column("Technique", width=22)
    table.add_column("File", max_width=50)
    table.add_column("Reduction", justify="right")

    for index, recommendation in enumerate(result["recommendations"][:top_n], 1):
        table.add_row(
            str(index),
            priority_markup(recommendation["priority"]),
            recommendation.get("smell") or "—",
            recommendation["technique"],
            recommendation["file_path"],
            human(recommendation.get("estimated_token_reduction", 0)),
        )
    console.print(table)


def print_code_smell_results(result: dict[str, Any], top_n: int) -> None:
    console.print(f"\n[bold]Files scanned:[/] {human(result['total_files_scanned'])}")
    console.print(f"[bold]Files with smells:[/] {result['files_with_smells']}\n")

    table = Table(title="Code Smell Results", show_lines=True)
    table.add_column("File", max_width=55, style="cyan")
    table.add_column("Tokens", justify="right", style="yellow")
    if dependency_enabled(result):
        table.add_column("Effective", justify="right", style="green")
    table.add_column("Language", width=12, style="magenta")
    table.add_column("Problems", max_width=35)
    table.add_column("Top Suggestions", max_width=45)

    for file_result in result["results"][:top_n]:
        row = [file_result["file"], human(file_result["tokens"])]
        if dependency_enabled(result):
            row.append(human(file_result.get("effective_token_size", file_result["tokens"])))
        row.extend(
            [
                file_result["language"],
                ", ".join(file_result["problems"][:3]) or "—",
                "; ".join(file_result["suggested_refactors"][:2]) or "—",
            ]
        )
        table.add_row(*row)
    console.print(table)


def print_heuristics_state(
    budget_info: dict[str, Any],
    *,
    title: str = "Heuristics Engine - Current State",
) -> None:
    fits = "[green]YES[/]" if budget_info["fits_context"] else "[red]NO[/]"
    console.print(
        Panel(
            f"[bold]Tokens:[/] {human(budget_info['total_tokens'])}   "
            f"[bold]Budget:[/] {human(budget_info['context_budget'])}   "
            f"[bold]Fits now:[/] {fits}",
            title=title,
            border_style="cyan",
        )
    )


def print_heuristic_results(result: dict[str, Any], limit: int = 15) -> None:
    heuristic_results = result.get("heuristic_results", [])
    if not heuristic_results:
        return

    table = Table(title=f"Files with Issues ({len(heuristic_results)} found)", show_lines=False)
    table.add_column("File", max_width=55, style="cyan")
    table.add_column("Tokens", justify="right", style="yellow")
    if dependency_enabled(result):
        table.add_column("Effective", justify="right", style="green")
    table.add_column("Problems", max_width=40)
    for heuristic_result in heuristic_results[:limit]:
        row = [heuristic_result["file"], human(heuristic_result["tokens"])]
        if dependency_enabled(result):
            row.append(
                human(heuristic_result.get("effective_token_size", heuristic_result["tokens"]))
            )
        row.append(", ".join(heuristic_result["problems"][:2]) or "—")
        table.add_row(*row)
    console.print(table)


def print_plan_overview(
    plan_info: dict[str, Any],
    *,
    plan_title: str = "Refactoring Plan",
) -> bool:
    if not plan_info.get("steps"):
        console.print("\n[green]No refactoring needed - project fits the context window.[/]")
        return False

    after_fits = "[green]YES[/]" if plan_info["fits_context_after"] else "[red]NO[/]"
    console.print(
        Panel(
            f"[bold]Steps:[/] {len(plan_info['steps'])}   "
            f"[bold]Est. reduction:[/] {human(plan_info['total_estimated_token_reduction'])} tokens   "
            f"[bold]Projected after:[/] {human(plan_info['projected_tokens_after'])} tokens   "
            f"[bold]Fits after:[/] {after_fits}",
            title=plan_title,
            border_style="green",
        )
    )
    return True


def print_plan_steps(
    plan_info: dict[str, Any],
    *,
    description_lines: int,
    reduction_label: str | None = None,
    truncate_marker: str | None = None,
) -> None:
    for step in plan_info["steps"]:
        console.print(f"\n[bold cyan]Step {step['step_number']}. {step['title']}[/]")
        console.print(f"  Techniques: {', '.join(step['techniques'])}")
        summary = f"  Files: {len(step['affected_files'])}"
        if reduction_label:
            summary += f"  |  {reduction_label}: {human(step['estimated_token_reduction'])} tokens"
        console.print(summary)
        description = step["description"].split("\n")
        for line in description[:description_lines]:
            console.print(f"  {line}")
        if truncate_marker and len(description) > description_lines:
            console.print(truncate_marker)
