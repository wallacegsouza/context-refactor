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
from ..rendering import (
    print_context_budget,
    print_largest_files,
    print_plan_overview,
    print_plan_steps,
    print_project_summary,
    print_refactor_recommendations,
    print_refactoring_candidates,
)
from ..runtime import typer
from ..shared import (
    build_tool_kwargs,
    print_analysis_context,
    run_tool,
)


def _render_analyze_result(result: dict[str, Any]) -> None:
    print_analysis_context(result)
    print_project_summary(result["project_summary"], result["context_budget"])
    print_largest_files(result)
    print_refactor_recommendations(result["refactor_recommendations"])

    plan = result.get("refactor_plan")
    if plan and print_plan_overview(plan):
        print_plan_steps(plan, description_lines=0)


def _render_budget_result(result: dict[str, Any]) -> None:
    print_analysis_context(result)
    print_context_budget(result)


def _render_candidates_result(result: dict[str, Any], top_n: int) -> None:
    print_analysis_context(result)
    print_refactoring_candidates(result, top_n)


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

        run_tool(
            analyze_project,
            output_json=output_json,
            render=_render_analyze_result,
            llm_context_size=context_size,
            safety_margin=safety_margin,
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

        run_tool(
            context_budget,
            output_json=output_json,
            render=_render_budget_result,
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

        run_tool(
            detect_refactor_candidates_tool,
            output_json=output_json,
            render=lambda result: _render_candidates_result(result, top_n),
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
