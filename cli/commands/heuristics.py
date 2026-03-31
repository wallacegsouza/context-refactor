"""Heuristics and planning CLI commands."""

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


def register_heuristics_commands(app: typer.Typer) -> None:
    @app.command()
    def smells(
        project_path: str = project_path_argument(),
        context_size: int = context_size_option(),
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
        """Detect code smells using the Heuristics Engine (pluggable rules)."""
        from mcp_server.tools import detect_code_smells

        path = resolve_path(project_path)
        result = detect_code_smells(
            project_path=path,
            llm_context_size=context_size,
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
        console.print(f"\n[bold]Files scanned:[/] {human(result['total_files_scanned'])}")
        console.print(f"[bold]Files with smells:[/] {result['files_with_smells']}\n")

        table = Table(title="Code Smell Results", show_lines=True)
        table.add_column("File", max_width=55, style="cyan")
        table.add_column("Tokens", justify="right", style="yellow")
        if _dependency_enabled(result):
            table.add_column("Effective", justify="right", style="green")
        table.add_column("Language", width=12, style="magenta")
        table.add_column("Problems", max_width=35)
        table.add_column("Top Suggestions", max_width=45)

        for file_result in result["results"][:top_n]:
            row = [file_result["file"], human(file_result["tokens"])]
            if _dependency_enabled(result):
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

    @app.command()
    def suggest(
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
        """Generate refactoring suggestions using the Heuristics Engine."""
        from mcp_server.tools import generate_refactor_suggestions

        path = resolve_path(project_path)
        result = generate_refactor_suggestions(
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

        budget_info = result["context_budget"]
        plan_info = result["refactor_plan"]
        print_analysis_scope(result)
        print_dependency_summary(result)

        fits = "[green]YES[/]" if budget_info["fits_context"] else "[red]NO[/]"
        console.print(
            Panel(
                f"[bold]Tokens:[/] {human(budget_info['total_tokens'])}   "
                f"[bold]Budget:[/] {human(budget_info['context_budget'])}   "
                f"[bold]Fits now:[/] {fits}",
                title="Heuristics Engine - Current State",
                border_style="cyan",
            )
        )

        heuristic_results = result.get("heuristic_results", [])
        if heuristic_results:
            table = Table(
                title=f"Files with Issues ({len(heuristic_results)} found)",
                show_lines=False,
            )
            table.add_column("File", max_width=55, style="cyan")
            table.add_column("Tokens", justify="right", style="yellow")
            if _dependency_enabled(result):
                table.add_column("Effective", justify="right", style="green")
            table.add_column("Problems", max_width=40)
            for heuristic_result in heuristic_results[:15]:
                row = [heuristic_result["file"], human(heuristic_result["tokens"])]
                if _dependency_enabled(result):
                    row.append(human(heuristic_result.get("effective_token_size", heuristic_result["tokens"])))
                row.append(", ".join(heuristic_result["problems"][:2]) or "—")
                table.add_row(*row)
            console.print(table)

        if not plan_info.get("steps"):
            console.print("\n[green]No refactoring needed - project fits the context window.[/]")
            return

        after_fits = "[green]YES[/]" if plan_info["fits_context_after"] else "[red]NO[/]"
        console.print(
            Panel(
                f"[bold]Steps:[/] {len(plan_info['steps'])}   "
                f"[bold]Est. reduction:[/] {human(plan_info['total_estimated_token_reduction'])} tokens   "
                f"[bold]Projected after:[/] {human(plan_info['projected_tokens_after'])} tokens   "
                f"[bold]Fits after:[/] {after_fits}",
                title="Refactoring Plan",
                border_style="green",
            )
        )

        for step in plan_info["steps"]:
            console.print(f"\n[bold cyan]Step {step['step_number']}. {step['title']}[/]")
            console.print(f"  Techniques: {', '.join(step['techniques'])}")
            console.print(
                f"  Files: {len(step['affected_files'])}  |  Est. reduction: {human(step['estimated_token_reduction'])} tokens"
            )
            for line in step["description"].split("\n")[:4]:
                console.print(f"  {line}")

    @app.command()
    def plan(
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
        """Generate a step-by-step refactoring plan."""
        from mcp_server.tools import generate_refactor_plan_tool

        path = resolve_path(project_path)
        result = generate_refactor_plan_tool(
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

        budget_info = result["context_budget"]
        plan_info = result["refactor_plan"]
        print_analysis_scope(result)
        print_dependency_summary(result)

        fits = "[green]YES[/]" if budget_info["fits_context"] else "[red]NO[/]"
        console.print(
            Panel(
                f"[bold]Tokens:[/] {human(budget_info['total_tokens'])}   "
                f"[bold]Budget:[/] {human(budget_info['context_budget'])}   "
                f"[bold]Fits now:[/] {fits}",
                title="Current State",
                border_style="cyan",
            )
        )

        if not plan_info.get("steps"):
            console.print("\n[green]No refactoring needed - project fits the context window.[/]")
            return

        after_fits = "[green]YES[/]" if plan_info["fits_context_after"] else "[red]NO[/]"
        console.print(
            Panel(
                f"[bold]Steps:[/] {len(plan_info['steps'])}   "
                f"[bold]Est. reduction:[/] {human(plan_info['total_estimated_token_reduction'])} tokens   "
                f"[bold]Projected after:[/] {human(plan_info['projected_tokens_after'])} tokens   "
                f"[bold]Fits after:[/] {after_fits}",
                title="Refactoring Plan",
                border_style="green",
            )
        )

        for step in plan_info["steps"]:
            console.print(f"\n[bold cyan]Step {step['step_number']}. {step['title']}[/]")
            console.print(f"  Techniques: {', '.join(step['techniques'])}")
            console.print(
                f"  Files: {len(step['affected_files'])}  |  Est. reduction: {human(step['estimated_token_reduction'])} tokens"
            )
            for line in step["description"].split("\n")[:5]:
                console.print(f"  {line}")
            if len(step["description"].split("\n")) > 5:
                console.print("  ... (truncated)")
