"""Analysis and legacy-planning MCP tools."""

from __future__ import annotations

from typing import Any

from context_refactor.refactor_planner import generate_refactor_plan
from mcp_server.tool_support_analysis import (
    compute_budget_from_totals,
    project_summary,
    run_token_analysis,
    shared_response_fields,
)
from mcp_server.tool_support_legacy import legacy_recommendations


def analyze_project(
    project_path: str,
    llm_context_size: int = 128_000,
    safety_margin: float = 0.80,
    estimator: str = "bytes",
    top_n: int = 50,
    analysis_profile: str = "default",
    config_path: str | None = None,
    exclude_dirs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    exclude_files: list[str] | None = None,
    include_categories: list[str] | None = None,
    exclude_categories: list[str] | None = None,
    dependency_mode: str | None = None,
    dependency_max_depth: int | None = None,
    dependency_max_multiplier: float | None = None,
    dependency_base_weight: float | None = None,
    dependency_depth_decay: float | None = None,
    dependency_depth_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Full project analysis: tokens, budget, recommendations, and plan."""
    all_files, all_dirs, totals = run_token_analysis(
        project_path,
        estimator=estimator,
        top_n=10_000,
        analysis_profile=analysis_profile,
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
    )
    budget = compute_budget_from_totals(totals, llm_context_size, safety_margin)
    recommendations = legacy_recommendations(all_files, project_path, totals)
    plan = generate_refactor_plan(recommendations, budget)

    return {
        **shared_response_fields(totals, include_hotspots=True),
        "project_summary": project_summary(totals, budget),
        "context_budget": budget.to_dict(),
        "largest_files": [file_info.to_dict() for file_info in all_files[: min(top_n, 25)]],
        "largest_directories": [directory.to_dict() for directory in all_dirs[:15]],
        "refactor_recommendations": [
            recommendation.to_dict()
            for recommendation in recommendations[:50]
        ],
        "refactor_plan": plan.to_dict(),
    }


def context_budget(
    project_path: str,
    llm_context_size: int = 128_000,
    safety_margin: float = 0.80,
    estimator: str = "bytes",
    analysis_profile: str = "default",
    config_path: str | None = None,
    exclude_dirs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    exclude_files: list[str] | None = None,
    include_categories: list[str] | None = None,
    exclude_categories: list[str] | None = None,
    dependency_mode: str | None = None,
    dependency_max_depth: int | None = None,
    dependency_max_multiplier: float | None = None,
    dependency_base_weight: float | None = None,
    dependency_depth_decay: float | None = None,
    dependency_depth_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Compute whether the project fits inside an LLM context window."""
    _, _, totals = run_token_analysis(
        project_path,
        estimator=estimator,
        top_n=1,
        analysis_profile=analysis_profile,
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
    )
    budget = compute_budget_from_totals(totals, llm_context_size, safety_margin)
    result = budget.to_dict()
    result.update(shared_response_fields(totals))
    return result


def detect_refactor_candidates_tool(
    project_path: str,
    estimator: str = "bytes",
    top_n: int = 50,
    analysis_profile: str = "default",
    config_path: str | None = None,
    exclude_dirs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    exclude_files: list[str] | None = None,
    include_categories: list[str] | None = None,
    exclude_categories: list[str] | None = None,
    dependency_mode: str | None = None,
    dependency_max_depth: int | None = None,
    dependency_max_multiplier: float | None = None,
    dependency_base_weight: float | None = None,
    dependency_depth_decay: float | None = None,
    dependency_depth_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Detect code smells and refactoring candidates."""
    file_infos, _, totals = run_token_analysis(
        project_path,
        estimator=estimator,
        top_n=10_000,
        analysis_profile=analysis_profile,
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
    )
    recommendations = legacy_recommendations(file_infos, project_path, totals)

    return {
        **shared_response_fields(totals, include_hotspots=True),
        "total_files_scanned": totals.get("files", 0),
        "candidates_found": len(recommendations),
        "recommendations": [recommendation.to_dict() for recommendation in recommendations[:top_n]],
    }


def generate_refactor_plan_tool(
    project_path: str,
    llm_context_size: int = 128_000,
    safety_margin: float = 0.80,
    estimator: str = "bytes",
    analysis_profile: str = "default",
    config_path: str | None = None,
    exclude_dirs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    exclude_files: list[str] | None = None,
    include_categories: list[str] | None = None,
    exclude_categories: list[str] | None = None,
    dependency_mode: str | None = None,
    dependency_max_depth: int | None = None,
    dependency_max_multiplier: float | None = None,
    dependency_base_weight: float | None = None,
    dependency_depth_decay: float | None = None,
    dependency_depth_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Generate a step-by-step refactoring plan to fit the context window."""
    file_infos, _, totals = run_token_analysis(
        project_path,
        estimator=estimator,
        top_n=10_000,
        analysis_profile=analysis_profile,
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
    )
    budget = compute_budget_from_totals(totals, llm_context_size, safety_margin)
    recommendations = legacy_recommendations(file_infos, project_path, totals)
    plan = generate_refactor_plan(recommendations, budget)

    return {
        **shared_response_fields(totals, include_hotspots=True),
        "context_budget": budget.to_dict(),
        "refactor_plan": plan.to_dict(),
    }


__all__ = [
    "analyze_project",
    "context_budget",
    "detect_refactor_candidates_tool",
    "generate_refactor_plan_tool",
]
