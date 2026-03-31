"""Heuristics and planning CLI commands."""

from __future__ import annotations

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
from ..rendering import (
    print_code_smell_results,
    print_heuristic_results,
    print_heuristics_state,
    print_plan_overview,
)
from ..runtime import console, typer
from ..shared import (
    build_tool_kwargs,
    human,
    print_analysis_context,
    print_json,
)


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

        result = detect_code_smells(
            llm_context_size=context_size,
            estimator=estimator,
            top_n=top_n,
            **build_tool_kwargs(
                project_path=project_path,
                profile=profile,
                config_path=config_path,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                exclude_files=exclude_files,
                include_categories=include_categories,
                exclude_categories=exclude_categories,
                dependency_mode=dependency_mode,
                dependency_max_depth=dependency_max_depth,
                dependency_max_multiplier=dependency_max_multiplier,
                dependency_base_weight=dependency_base_weight,
                dependency_depth_decay=dependency_depth_decay,
                dependency_depth_weights=dependency_depth_weights,
            ),
        )

        if output_json:
            print_json(result)
            return

        print_analysis_context(result)
        print_code_smell_results(result, top_n)

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

        result = generate_refactor_suggestions(
            llm_context_size=context_size,
            safety_margin=safety_margin,
            estimator=estimator,
            **build_tool_kwargs(
                project_path=project_path,
                profile=profile,
                config_path=config_path,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                exclude_files=exclude_files,
                include_categories=include_categories,
                exclude_categories=exclude_categories,
                dependency_mode=dependency_mode,
                dependency_max_depth=dependency_max_depth,
                dependency_max_multiplier=dependency_max_multiplier,
                dependency_base_weight=dependency_base_weight,
                dependency_depth_decay=dependency_depth_decay,
                dependency_depth_weights=dependency_depth_weights,
            ),
        )

        if output_json:
            print_json(result)
            return

        budget_info = result["context_budget"]
        plan_info = result["refactor_plan"]
        print_analysis_context(result)
        print_heuristics_state(budget_info)
        print_heuristic_results(result)

        if not print_plan_overview(plan_info):
            return

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

        result = generate_refactor_plan_tool(
            llm_context_size=context_size,
            safety_margin=safety_margin,
            estimator=estimator,
            **build_tool_kwargs(
                project_path=project_path,
                profile=profile,
                config_path=config_path,
                exclude_dirs=exclude_dirs,
                exclude_globs=exclude_globs,
                exclude_files=exclude_files,
                include_categories=include_categories,
                exclude_categories=exclude_categories,
                dependency_mode=dependency_mode,
                dependency_max_depth=dependency_max_depth,
                dependency_max_multiplier=dependency_max_multiplier,
                dependency_base_weight=dependency_base_weight,
                dependency_depth_decay=dependency_depth_decay,
                dependency_depth_weights=dependency_depth_weights,
            ),
        )

        if output_json:
            print_json(result)
            return

        budget_info = result["context_budget"]
        plan_info = result["refactor_plan"]
        print_analysis_context(result)
        print_heuristics_state(budget_info, title="Current State")

        if not print_plan_overview(plan_info):
            return

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
