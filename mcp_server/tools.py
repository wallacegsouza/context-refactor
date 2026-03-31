"""MCP tool definitions for ContextRefactor.

Each public function corresponds to one MCP tool exposed via the server.
They receive primitive arguments, call into the ``context_refactor`` core
package, and return JSON-serialisable dicts.
"""

from __future__ import annotations

from typing import Any

from context_refactor.analyzer import analyze_tokens
from context_refactor.context_budget import compute_budget
from context_refactor.refactor_engine import detect_refactor_candidates
from context_refactor.refactor_planner import generate_refactor_plan

# HeuristicsEngine is imported lazily inside tool functions so that the
# existing four tools remain importable even before refactor_heuristics.py
# is present (useful during incremental development).


def _analysis_kwargs(
    analysis_profile: str,
    config_path: str | None,
    exclude_dirs: list[str] | None,
    exclude_globs: list[str] | None,
    exclude_files: list[str] | None,
    include_categories: list[str] | None,
    exclude_categories: list[str] | None,
) -> dict[str, Any]:
    return {
        "analysis_profile": analysis_profile,
        "config_path": config_path,
        "exclude_dirs": exclude_dirs,
        "exclude_globs": exclude_globs,
        "exclude_files": exclude_files,
        "include_categories": include_categories,
        "exclude_categories": exclude_categories,
    }


def _dependency_kwargs(
    dependency_mode: str | None,
    dependency_max_depth: int | None,
    dependency_max_multiplier: float | None,
    dependency_base_weight: float | None,
    dependency_depth_decay: float | None,
    dependency_depth_weights: list[float] | None,
) -> dict[str, Any]:
    return {
        "dependency_mode": dependency_mode,
        "dependency_max_depth": dependency_max_depth,
        "dependency_max_multiplier": dependency_max_multiplier,
        "dependency_base_weight": dependency_base_weight,
        "dependency_depth_decay": dependency_depth_decay,
        "dependency_depth_weights": dependency_depth_weights,
    }


def _dependency_rules_enabled(totals: dict[str, Any]) -> bool:
    mode = totals.get("dependency_analysis", {}).get("mode")
    return mode in {"blended", "weighted"}


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
    analysis_kwargs = _analysis_kwargs(
        analysis_profile=analysis_profile,
        config_path=config_path,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        exclude_files=exclude_files,
        include_categories=include_categories,
        exclude_categories=exclude_categories,
    )
    all_files, all_dirs, totals = analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=10_000,
        **analysis_kwargs,
        **_dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )

    total_tokens = totals.get("tokens", 0)
    total_files = totals.get("files", 0)

    budget = compute_budget(
        total_tokens=total_tokens,
        total_files=total_files,
        llm_context_size=llm_context_size,
        safety_margin=safety_margin,
    )

    recommendations = detect_refactor_candidates(
        all_files,
        project_path,
        enable_dependency_rules=_dependency_rules_enabled(totals),
    )
    plan = generate_refactor_plan(recommendations, budget)

    return {
        "report_schema_version": totals.get("report_schema_version", 1),
        "compatibility_mode": totals.get("compatibility_mode", "legacy"),
        "analysis_scope": totals.get("analysis_scope", {}),
        "noise_summary": totals.get("noise_summary", {}),
        "signal_score": totals.get("signal_score", {}),
        "category_counts": totals.get("category_counts", {}),
        "category_tokens": totals.get("category_tokens", {}),
        "dependency_analysis": totals.get("dependency_analysis", {}),
        "project_summary": {
            "files": total_files,
            "total_tokens": total_tokens,
            "context_budget": budget.context_budget,
            "fits_context": budget.fits_context,
        },
        "context_budget": budget.to_dict(),
        "largest_files": [f.to_dict() for f in all_files[: min(top_n, 25)]],
        "largest_directories": [d.to_dict() for d in all_dirs[:15]],
        "dependency_hotspots": totals.get("dependency_analysis", {}).get("hotspots", []),
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
    _, _, totals = analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=1,
        **_analysis_kwargs(
            analysis_profile=analysis_profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
        **_dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )

    budget = compute_budget(
        total_tokens=totals.get("tokens", 0),
        total_files=totals.get("files", 0),
        llm_context_size=llm_context_size,
        safety_margin=safety_margin,
    )
    result = budget.to_dict()
    result["analysis_scope"] = totals.get("analysis_scope", {})
    result["noise_summary"] = totals.get("noise_summary", {})
    result["signal_score"] = totals.get("signal_score", {})
    result["category_counts"] = totals.get("category_counts", {})
    result["category_tokens"] = totals.get("category_tokens", {})
    result["report_schema_version"] = totals.get("report_schema_version", 1)
    result["compatibility_mode"] = totals.get("compatibility_mode", "legacy")
    result["dependency_analysis"] = totals.get("dependency_analysis", {})
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
    file_infos, _, totals = analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=10_000,
        **_analysis_kwargs(
            analysis_profile=analysis_profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
        **_dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )
    recommendations = detect_refactor_candidates(
        file_infos,
        project_path,
        enable_dependency_rules=_dependency_rules_enabled(totals),
    )

    return {
        "report_schema_version": totals.get("report_schema_version", 1),
        "compatibility_mode": totals.get("compatibility_mode", "legacy"),
        "analysis_scope": totals.get("analysis_scope", {}),
        "noise_summary": totals.get("noise_summary", {}),
        "signal_score": totals.get("signal_score", {}),
        "category_counts": totals.get("category_counts", {}),
        "category_tokens": totals.get("category_tokens", {}),
        "dependency_analysis": totals.get("dependency_analysis", {}),
        "dependency_hotspots": totals.get("dependency_analysis", {}).get("hotspots", []),
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
    file_infos, _, totals = analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=10_000,
        **_analysis_kwargs(
            analysis_profile=analysis_profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
        **_dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )

    total_tokens = totals.get("tokens", 0)
    total_files = totals.get("files", 0)

    budget = compute_budget(
        total_tokens=total_tokens,
        total_files=total_files,
        llm_context_size=llm_context_size,
        safety_margin=safety_margin,
    )

    recommendations = detect_refactor_candidates(
        file_infos,
        project_path,
        enable_dependency_rules=_dependency_rules_enabled(totals),
    )
    plan = generate_refactor_plan(recommendations, budget)

    return {
        "report_schema_version": totals.get("report_schema_version", 1),
        "compatibility_mode": totals.get("compatibility_mode", "legacy"),
        "analysis_scope": totals.get("analysis_scope", {}),
        "noise_summary": totals.get("noise_summary", {}),
        "signal_score": totals.get("signal_score", {}),
        "category_counts": totals.get("category_counts", {}),
        "category_tokens": totals.get("category_tokens", {}),
        "dependency_analysis": totals.get("dependency_analysis", {}),
        "dependency_hotspots": totals.get("dependency_analysis", {}).get("hotspots", []),
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
    from context_refactor.refactor_heuristics import HeuristicsEngine

    file_infos, _, totals = analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=10_000,
        **_analysis_kwargs(
            analysis_profile=analysis_profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
        **_dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )

    dependency_mode_resolved = totals.get("dependency_analysis", {}).get("mode")
    engine = HeuristicsEngine(
        context_window_size=llm_context_size,
        rank_by_dependency=dependency_mode_resolved in {"blended", "weighted"},
    )
    results = engine.analyze_project(file_infos, project_path)

    return {
        "report_schema_version": totals.get("report_schema_version", 1),
        "compatibility_mode": totals.get("compatibility_mode", "legacy"),
        "analysis_scope": totals.get("analysis_scope", {}),
        "noise_summary": totals.get("noise_summary", {}),
        "signal_score": totals.get("signal_score", {}),
        "category_counts": totals.get("category_counts", {}),
        "category_tokens": totals.get("category_tokens", {}),
        "dependency_analysis": totals.get("dependency_analysis", {}),
        "dependency_hotspots": totals.get("dependency_analysis", {}).get("hotspots", []),
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
    from context_refactor.refactor_heuristics import HeuristicsEngine

    file_infos, _, totals = analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=10_000,
        **_analysis_kwargs(
            analysis_profile=analysis_profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
        **_dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )

    total_tokens = totals.get("tokens", 0)
    total_files = totals.get("files", 0)

    budget = compute_budget(
        total_tokens=total_tokens,
        total_files=total_files,
        llm_context_size=llm_context_size,
        safety_margin=safety_margin,
    )

    dependency_mode_resolved = totals.get("dependency_analysis", {}).get("mode")
    engine = HeuristicsEngine(
        context_window_size=llm_context_size,
        rank_by_dependency=dependency_mode_resolved in {"blended", "weighted"},
    )
    results = engine.analyze_project(file_infos, project_path)
    plan = engine.generate_plan(results, budget)

    return {
        "report_schema_version": totals.get("report_schema_version", 1),
        "compatibility_mode": totals.get("compatibility_mode", "legacy"),
        "analysis_scope": totals.get("analysis_scope", {}),
        "noise_summary": totals.get("noise_summary", {}),
        "signal_score": totals.get("signal_score", {}),
        "category_counts": totals.get("category_counts", {}),
        "category_tokens": totals.get("category_tokens", {}),
        "dependency_analysis": totals.get("dependency_analysis", {}),
        "dependency_hotspots": totals.get("dependency_analysis", {}).get("hotspots", []),
        "context_budget": budget.to_dict(),
        "heuristic_results": [r.to_dict() for r in results[:50]],
        "refactor_plan": plan.to_dict(),
    }
