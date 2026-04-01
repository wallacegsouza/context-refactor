"""MCP tool definitions for ContextRefactor.

Each public function corresponds to one MCP tool exposed via the server.
They receive primitive arguments, call into the ``context_refactor`` core
package, and return JSON-serialisable dicts.
"""

from __future__ import annotations

from typing import Any

from context_refactor.refactor_planner import generate_refactor_plan
from mcp_server.tool_support import (
    compute_budget_from_totals,
    create_heuristics_engine,
    legacy_recommendations,
    project_summary,
    run_token_analysis,
    shared_response_fields,
)

# HeuristicsEngine is imported lazily inside tool functions so that the
# existing four tools remain importable even before refactor_heuristics.py
# is present (useful during incremental development).


# ── Tool 1: analyze_project ──────────────────────────────────────────────────


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
    """Full project analysis: tokens, budget, recommendations, and plan.

    MCP tool name: ``context_refactor.analyze_project``
    """
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
        "largest_files": [f.to_dict() for f in all_files[: min(top_n, 25)]],
        "largest_directories": [d.to_dict() for d in all_dirs[:15]],
        "refactor_recommendations": [r.to_dict() for r in recommendations[:50]],
        "refactor_plan": plan.to_dict(),
    }


# ── Tool 2: context_budget ───────────────────────────────────────────────────


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
    """Compute whether the project fits inside an LLM context window.

    MCP tool name: ``context_refactor.context_budget``
    """
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


# ── Tool 3: detect_refactor_candidates ────────────────────────────────────────


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
    """Detect code smells and refactoring candidates.

    MCP tool name: ``context_refactor.detect_refactor_candidates``
    """
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
        "recommendations": [r.to_dict() for r in recommendations[:top_n]],
    }


# ── Tool 4: generate_refactor_plan ───────────────────────────────────────────


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
    """Generate a step-by-step refactoring plan to fit the context window.

    MCP tool name: ``context_refactor.generate_refactor_plan``
    """
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


# ── Tool 5: detect_code_smells ────────────────────────────────────────────────


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
    """Run the HeuristicsEngine and return per-file code smell results.

    Uses pluggable rule classes with context-window-relative thresholds.

    MCP tool name: ``context_refactor.detect_code_smells``
    """
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
        "results": [r.to_dict() for r in results[:top_n]],
    }


# ── Tool 6: generate_refactor_suggestions ────────────────────────────────────


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
    """Generate human-readable refactoring suggestions and a step-by-step plan.

    Runs the HeuristicsEngine then passes all findings to the existing
    :func:`~context_refactor.refactor_planner.generate_refactor_plan` planner.

    MCP tool name: ``context_refactor.generate_refactor_suggestions``
    """
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
        "heuristic_results": [r.to_dict() for r in results[:50]],
        "refactor_plan": plan.to_dict(),
    }
