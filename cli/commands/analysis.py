"""Analysis and candidate-related CLI commands."""

from __future__ import annotations

from typing import Any

from ..options import (
    config_path_option,
    context_size_option,
    dependency_base_weight_option,
    dependency_depth_decay_option,
    dependency_depth_weights_option,
    dependency_max_depth_option,
    dependency_max_multiplier_option,
    dependency_mode_option,
    estimator_option,
    exclude_categories_option,
    exclude_dirs_option,
    exclude_files_option,
    exclude_globs_option,
    include_categories_option,
    output_json_option,
    profile_option,
    project_path_argument,
    safety_margin_option,
    top_n_option,
)
from ..runtime import Panel, Table, console, typer
from ..shared import (
    analysis_options,
    dependency_options,
    human,
    print_analysis_scope,
    print_dependency_summary,
    print_json,
    resolve_path,
)


def _dependency_enabled(result: dict[str, Any]) -> bool:
    return bool(result.get("dependency_analysis", {}).get("enabled"))


def _priority_markup(priority: str) -> str:
    color = {
        "critical": "red",
        "high": "yellow",
        "medium": "cyan",
        "low": "dim",
    }.get(priority, "")
    return f"[{color}]{priority}[/]"


def register_analysis_commands(app: typer.Typer) -> None:
    @app.command()
    def analyze(
        project_path: str = project_path_argument(),
        context_size: int = context_size_option(),
        safety_margin: float = safety_margin_option(),
        estimator: str = estimator_option(),
        output_json: bool = output_json_option(),
        top_n: int = top_n_option(),
        profile: str = profile_option(),
        config_path: str | None = config_path_option(),
        exclude_dirs: str | None = exclude_dirs_option(),
        exclude_globs: str | None = exclude_globs_option(),
        exclude_files: str | None = exclude_files_option(),
        include_categories: str | None = include_categories_option(),
        exclude_categories: str | None = exclude_categories_option(),
        dependency_mode: str | None = dependency_mode_option(),
        dependency_max_depth: int | None = dependency_max_depth_option(),
        dependency_max_multiplier: float | None = dependency_max_multiplier_option(),
        dependency_base_weight: float | None = dependency_base_weight_option(),
        dependency_depth_decay: float | None = dependency_depth_decay_option(),
        dependency_depth_weights: str | None = dependency_depth_weights_option(),
    ) -> None:
        """Full project analysis with recommendations and refactoring plan."""
        from mcp_server.tools import analyze_project

        path = resolve_path(project_path)
        result = analyze_project(
            project_path=path,
            llm_context_size=context_size,
            safety_margin=safety_margin,
            estimator=estimator,
            top_n=top_n,
            **analysis_options(
                profile=profile,
                config_path=config_path,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                exclude_files=exclude_files,
                include_categories=include_categories,
                exclude_categories=exclude_categories,
            ),
            **dependency_options(
                mode=dependency_mode,
                max_depth=dependency_max_depth,
                max_multiplier=dependency_max_multiplier,
                base_weight=dependency_base_weight,
                depth_decay=dependency_depth_decay,
                depth_weights=dependency_depth_weights,
            ),
        )

        if output_json:
            print_json(result)
            return

        summary = result["project_summary"]
        budget = result["context_budget"]
        print_analysis_scope(result)
        print_dependency_summary(result)

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

        table = Table(title="Largest Files by Tokens", show_lines=False)
        table.add_column("File", style="cyan", no_wrap=True, max_width=70)
        table.add_column("Category", style="magenta")
        table.add_column("Tokens", justify="right", style="yellow")
        if _dependency_enabled(result):
            table.add_column("Effective", justify="right", style="green")
        for file_info in result["largest_files"][:20]:
            row = [file_info["path"], file_info["category"], human(file_info["tokens"])]
            if _dependency_enabled(result):
                row.append(human(file_info.get("effective_token_size", file_info["tokens"])))
            table.add_row(*row)
        console.print(table)

        recommendations = result["refactor_recommendations"]
        if recommendations:
            recommendation_table = Table(
                title=f"Refactor Recommendations ({len(recommendations)} found)",
                show_lines=True,
            )
            recommendation_table.add_column("#", justify="right", width=4)
            recommendation_table.add_column("Priority", width=10)
            recommendation_table.add_column("Technique", width=22)
            recommendation_table.add_column("File", max_width=50)
            recommendation_table.add_column("Description", max_width=60)
            for index, recommendation in enumerate(recommendations[:25], 1):
                recommendation_table.add_row(
                    str(index),
                    _priority_markup(recommendation["priority"]),
                    recommendation["technique"],
                    recommendation["file_path"],
                    recommendation["description"][:80],
                )
            console.print(recommendation_table)

        plan = result.get("refactor_plan")
        if plan and plan.get("steps"):
            console.print(
                Panel(
                    f"[bold]Steps:[/] {len(plan['steps'])}   "
                    f"[bold]Est. reduction:[/] {human(plan['total_estimated_token_reduction'])} tokens   "
                    f"[bold]Projected after:[/] {human(plan['projected_tokens_after'])} tokens   "
                    f"[bold]Fits after:[/] {'[green]YES[/]' if plan['fits_context_after'] else '[red]NO[/]'}",
                    title="Refactoring Plan",
                    border_style="green",
                )
            )
            for step in plan["steps"]:
                console.print(
                    f"\n  [bold cyan]Step {step['step_number']}:[/] {step['title']}\n"
                    f"  Techniques: {', '.join(step['techniques'])}\n"
                    f"  Files affected: {len(step['affected_files'])}"
                )

    @app.command()
    def budget(
        project_path: str = project_path_argument(),
        context_size: int = context_size_option(),
        safety_margin: float = safety_margin_option(),
        estimator: str = estimator_option(),
        output_json: bool = output_json_option(),
        profile: str = profile_option(),
        config_path: str | None = config_path_option(),
        exclude_dirs: str | None = exclude_dirs_option(),
        exclude_globs: str | None = exclude_globs_option(),
        exclude_files: str | None = exclude_files_option(),
        include_categories: str | None = include_categories_option(),
        exclude_categories: str | None = exclude_categories_option(),
        dependency_mode: str | None = dependency_mode_option(),
        dependency_max_depth: int | None = dependency_max_depth_option(),
        dependency_max_multiplier: float | None = dependency_max_multiplier_option(),
        dependency_base_weight: float | None = dependency_base_weight_option(),
        dependency_depth_decay: float | None = dependency_depth_decay_option(),
        dependency_depth_weights: str | None = dependency_depth_weights_option(),
    ) -> None:
        """Check if the project fits inside an LLM context window."""
        from mcp_server.tools import context_budget

        path = resolve_path(project_path)
        result = context_budget(
            project_path=path,
            llm_context_size=context_size,
            safety_margin=safety_margin,
            estimator=estimator,
            **analysis_options(
                profile=profile,
                config_path=config_path,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                exclude_files=exclude_files,
                include_categories=include_categories,
                exclude_categories=exclude_categories,
            ),
            **dependency_options(
                mode=dependency_mode,
                max_depth=dependency_max_depth,
                max_multiplier=dependency_max_multiplier,
                base_weight=dependency_base_weight,
                depth_decay=dependency_depth_decay,
                depth_weights=dependency_depth_weights,
            ),
        )

        if output_json:
            print_json(result)
            return

        print_analysis_scope(result)
        print_dependency_summary(result)
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

    @app.command()
    def candidates(
        project_path: str = project_path_argument(),
        estimator: str = estimator_option(),
        top_n: int = top_n_option(),
        output_json: bool = output_json_option(),
        profile: str = profile_option(),
        config_path: str | None = config_path_option(),
        exclude_dirs: str | None = exclude_dirs_option(),
        exclude_globs: str | None = exclude_globs_option(),
        exclude_files: str | None = exclude_files_option(),
        include_categories: str | None = include_categories_option(),
        exclude_categories: str | None = exclude_categories_option(),
        dependency_mode: str | None = dependency_mode_option(),
        dependency_max_depth: int | None = dependency_max_depth_option(),
        dependency_max_multiplier: float | None = dependency_max_multiplier_option(),
        dependency_base_weight: float | None = dependency_base_weight_option(),
        dependency_depth_decay: float | None = dependency_depth_decay_option(),
        dependency_depth_weights: str | None = dependency_depth_weights_option(),
    ) -> None:
        """Detect code smells and refactoring candidates."""
        from mcp_server.tools import detect_refactor_candidates_tool

        path = resolve_path(project_path)
        result = detect_refactor_candidates_tool(
            project_path=path,
            estimator=estimator,
            top_n=top_n,
            **analysis_options(
                profile=profile,
                config_path=config_path,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                exclude_files=exclude_files,
                include_categories=include_categories,
                exclude_categories=exclude_categories,
            ),
            **dependency_options(
                mode=dependency_mode,
                max_depth=dependency_max_depth,
                max_multiplier=dependency_max_multiplier,
                base_weight=dependency_base_weight,
                depth_decay=dependency_depth_decay,
                depth_weights=dependency_depth_weights,
            ),
        )

        if output_json:
            print_json(result)
            return

        print_analysis_scope(result)
        print_dependency_summary(result)
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
                _priority_markup(recommendation["priority"]),
                recommendation.get("smell") or "—",
                recommendation["technique"],
                recommendation["file_path"],
                human(recommendation.get("estimated_token_reduction", 0)),
            )
        console.print(table)
