"""Analyzer public facade for token and dependency-aware project analysis."""

from __future__ import annotations

from typing import Any

from .analyzer_classification import classify_file
from .analyzer_config import (
    DEFAULT_CONFIG_FILENAME,
    DEPENDENCY_METRICS_VERSION,
    NOISE_REDUCTION_DIRS,
    NOISE_REDUCTION_FILES,
    NOISE_REDUCTION_GLOBS,
    PROFILE_DEFAULTS,
    REPORT_SCHEMA_VERSION,
    VALID_DEPENDENCY_MODES,
    resolve_analysis_scope,
    resolve_dependency_options,
)
from .analyzer_metrics import (
    aggregate_directories,
    apply_dependency_analysis,
    build_file_infos,
    filter_file_infos,
    initialize_analysis_totals,
    merge_dependency_metrics,
    summarize_file_infos,
)
from .analyzer_runner import run_token_report
from .models import DirectoryTokenInfo, FileTokenInfo

_DEFAULT_CONFIG_FILENAME = DEFAULT_CONFIG_FILENAME
_REPORT_SCHEMA_VERSION = REPORT_SCHEMA_VERSION
_DEPENDENCY_METRICS_VERSION = DEPENDENCY_METRICS_VERSION
_VALID_DEPENDENCY_MODES = VALID_DEPENDENCY_MODES
_NOISE_REDUCTION_DIRS = NOISE_REDUCTION_DIRS
_NOISE_REDUCTION_GLOBS = NOISE_REDUCTION_GLOBS
_NOISE_REDUCTION_FILES = NOISE_REDUCTION_FILES
_PROFILE_DEFAULTS = PROFILE_DEFAULTS
_resolve_analysis_scope = resolve_analysis_scope
_resolve_dependency_options = resolve_dependency_options
_merge_dependency_metrics = merge_dependency_metrics
_aggregate_directories = aggregate_directories
_run_token_report = run_token_report

__all__ = ["analyze_tokens", "classify_file"]


def analyze_tokens(
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
) -> tuple[list[FileTokenInfo], list[DirectoryTokenInfo], dict[str, Any]]:
    """Run token analysis and return classified results."""
    analysis_scope = _resolve_analysis_scope(
        project_path=project_path,
        analysis_profile=analysis_profile,
        config_path=config_path,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        exclude_files=exclude_files,
        include_categories=include_categories,
        exclude_categories=exclude_categories,
    )
    dependency_options = _resolve_dependency_options(
        project_path=project_path,
        config_path=config_path,
        dependency_mode=dependency_mode,
        dependency_max_depth=dependency_max_depth,
        dependency_max_multiplier=dependency_max_multiplier,
        dependency_base_weight=dependency_base_weight,
        dependency_depth_decay=dependency_depth_decay,
        dependency_depth_weights=dependency_depth_weights,
    )
    raw = _run_token_report(
        project_path,
        estimator=estimator,
        extra_exclude_dirs=analysis_scope["exclude_dirs"],
        extra_exclude_globs=analysis_scope["exclude_globs"],
        extra_exclude_files=analysis_scope["exclude_files"],
    )
    totals: dict[str, Any] = dict(raw.get("totals", {}))
    file_infos = build_file_infos(raw.get("files", []))
    scanner_summary = summarize_file_infos(file_infos)
    file_infos = filter_file_infos(
        file_infos,
        include_categories=analysis_scope["include_categories"],
        exclude_categories=analysis_scope["exclude_categories"],
    )
    dir_infos = _aggregate_directories(file_infos)
    filtered_summary = summarize_file_infos(file_infos)
    initialize_analysis_totals(
        totals,
        analysis_scope=analysis_scope,
        dependency_options=dependency_options,
        scanner_summary=scanner_summary,
        filtered_summary=filtered_summary,
        report_schema_version=_REPORT_SCHEMA_VERSION,
        dependency_metrics_version=_DEPENDENCY_METRICS_VERSION,
    )

    if dependency_options["enabled"]:
        file_infos, dependency_metadata = apply_dependency_analysis(
            project_path=project_path,
            file_infos=file_infos,
            dependency_options=dependency_options,
            top_n=top_n,
        )
        totals["compatibility_mode"] = dependency_metadata["compatibility_mode"]
        totals["dependency_analysis"].update(dependency_metadata["dependency_analysis"])

    file_infos.sort(key=lambda f: f.tokens, reverse=True)
    dir_infos.sort(key=lambda d: d.tokens, reverse=True)

    return file_infos[:top_n], dir_infos[:top_n], totals
