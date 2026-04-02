"""Heuristics-driven MCP tools."""

from __future__ import annotations

from typing import Any

from mcp_server.tool_support_analysis import (
    compute_budget_from_totals,
    run_token_analysis,
    shared_response_fields,
)
from mcp_server.tool_support_heuristics import create_heuristics_engine


def detect_code_smells(
    project_path: str,
    llm_context_size: int = 128_000,
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
    """Run the HeuristicsEngine and return per-file code smell results."""
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
    engine = create_heuristics_engine(llm_context_size, totals)
    results = engine.analyze_project(file_infos, project_path)

    return {
        **shared_response_fields(totals, include_hotspots=True),
        "total_files_scanned": totals.get("files", 0),
        "files_with_smells": len(results),
        "results": [result.to_dict() for result in results[:top_n]],
    }


def generate_refactor_suggestions(
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
    """Generate human-readable refactoring suggestions and a step-by-step plan."""
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
    engine = create_heuristics_engine(llm_context_size, totals)
    results = engine.analyze_project(file_infos, project_path)
    plan = engine.generate_plan(results, budget)

    return {
        **shared_response_fields(totals, include_hotspots=True),
        "context_budget": budget.to_dict(),
        "heuristic_results": [result.to_dict() for result in results[:50]],
        "refactor_plan": plan.to_dict(),
    }


__all__ = [
    "detect_code_smells",
    "generate_refactor_suggestions",
]
