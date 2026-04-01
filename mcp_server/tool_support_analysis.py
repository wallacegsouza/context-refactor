"""Analysis-domain support helpers for MCP tool wrappers."""

from __future__ import annotations

from typing import Any

from context_refactor.analyzer import analyze_tokens
from context_refactor.context_budget import compute_budget


def analysis_kwargs(
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


def dependency_kwargs(
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


def run_token_analysis(
    project_path: str,
    estimator: str,
    top_n: int,
    *,
    analysis_profile: str,
    config_path: str | None,
    exclude_dirs: list[str] | None,
    exclude_globs: list[str] | None,
    exclude_files: list[str] | None,
    include_categories: list[str] | None,
    exclude_categories: list[str] | None,
    dependency_mode: str | None,
    dependency_max_depth: int | None,
    dependency_max_multiplier: float | None,
    dependency_base_weight: float | None,
    dependency_depth_decay: float | None,
    dependency_depth_weights: list[float] | None,
) -> tuple[list[Any], list[Any], dict[str, Any]]:
    return analyze_tokens(
        project_path,
        estimator=estimator,
        top_n=top_n,
        **analysis_kwargs(
            analysis_profile=analysis_profile,
            config_path=config_path,
            exclude_dirs=exclude_dirs,
            exclude_globs=exclude_globs,
            exclude_files=exclude_files,
            include_categories=include_categories,
            exclude_categories=exclude_categories,
        ),
        **dependency_kwargs(
            dependency_mode=dependency_mode,
            dependency_max_depth=dependency_max_depth,
            dependency_max_multiplier=dependency_max_multiplier,
            dependency_base_weight=dependency_base_weight,
            dependency_depth_decay=dependency_depth_decay,
            dependency_depth_weights=dependency_depth_weights,
        ),
    )


def compute_budget_from_totals(
    totals: dict[str, Any],
    llm_context_size: int,
    safety_margin: float,
):
    return compute_budget(
        total_tokens=totals.get("tokens", 0),
        total_files=totals.get("files", 0),
        llm_context_size=llm_context_size,
        safety_margin=safety_margin,
    )


def shared_response_fields(
    totals: dict[str, Any],
    *,
    include_hotspots: bool = False,
) -> dict[str, Any]:
    payload = {
        "report_schema_version": totals.get("report_schema_version", 1),
        "compatibility_mode": totals.get("compatibility_mode", "legacy"),
        "analysis_scope": totals.get("analysis_scope", {}),
        "noise_summary": totals.get("noise_summary", {}),
        "signal_score": totals.get("signal_score", {}),
        "category_counts": totals.get("category_counts", {}),
        "category_tokens": totals.get("category_tokens", {}),
        "dependency_analysis": totals.get("dependency_analysis", {}),
    }
    if include_hotspots:
        payload["dependency_hotspots"] = totals.get("dependency_analysis", {}).get("hotspots", [])
    return payload


def project_summary(totals: dict[str, Any], budget: Any) -> dict[str, Any]:
    return {
        "files": totals.get("files", 0),
        "total_tokens": totals.get("tokens", 0),
        "context_budget": budget.context_budget,
        "fits_context": budget.fits_context,
    }


__all__ = [
    "analysis_kwargs",
    "compute_budget_from_totals",
    "dependency_kwargs",
    "project_summary",
    "run_token_analysis",
    "shared_response_fields",
]
