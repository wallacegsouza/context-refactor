"""Analysis pipeline helpers for file summaries and dependency enrichment."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .analyzer_classification import classify_file
from .dependency_analyzer import build_dependency_graph, compute_dependency_weights
from .models import DirectoryTokenInfo, FileCategory, FileTokenInfo


@dataclass(frozen=True)
class FileCollectionSummary:
    """Summarized counts and token totals for a file collection."""

    files: int
    tokens: int
    category_counts: dict[str, int]
    category_tokens: dict[str, int]


def build_file_infos(raw_files: Sequence[dict[str, Any]]) -> list[FileTokenInfo]:
    """Convert raw token-report entries into classified file infos."""
    file_infos: list[FileTokenInfo] = []
    for entry in raw_files:
        path = entry.get("path", "")
        ext = entry.get("ext", "")
        file_infos.append(
            FileTokenInfo(
                path=path,
                ext=ext,
                tokens=entry.get("tokens", 0),
                bytes_=entry.get("bytes", 0),
                chars=entry.get("chars", 0),
                category=classify_file(path, ext),
            )
        )
    return file_infos


def summarize_file_infos(file_infos: Sequence[FileTokenInfo]) -> FileCollectionSummary:
    """Build aggregate counts and token totals for a collection of files."""
    category_counts: dict[str, int] = defaultdict(int)
    category_tokens: dict[str, int] = defaultdict(int)

    for file_info in file_infos:
        category_counts[file_info.category.value] += 1
        category_tokens[file_info.category.value] += file_info.tokens

    return FileCollectionSummary(
        files=len(file_infos),
        tokens=sum(file_info.tokens for file_info in file_infos),
        category_counts=dict(category_counts),
        category_tokens=dict(category_tokens),
    )


def filter_file_infos(
    file_infos: Sequence[FileTokenInfo],
    include_categories: Sequence[str],
    exclude_categories: Sequence[str],
) -> list[FileTokenInfo]:
    """Apply category-based include and exclude filters to file infos."""
    include_category_set = set(include_categories)
    exclude_category_set = set(exclude_categories)

    filtered = list(file_infos)
    if include_category_set:
        filtered = [file_info for file_info in filtered if file_info.category.value in include_category_set]
    if exclude_category_set:
        filtered = [file_info for file_info in filtered if file_info.category.value not in exclude_category_set]
    return filtered


def merge_dependency_metrics(
    file_infos: Sequence[FileTokenInfo],
    dependency_results: dict[str, Any],
) -> list[FileTokenInfo]:
    """Merge dependency metrics back into tokenized file infos."""
    merged: list[FileTokenInfo] = []
    for file_info in file_infos:
        result = dependency_results.get(file_info.path)
        if result is None:
            merged.append(file_info)
            continue

        merged.append(
            FileTokenInfo(
                path=file_info.path,
                ext=file_info.ext,
                tokens=file_info.tokens,
                bytes_=file_info.bytes_,
                chars=file_info.chars,
                category=file_info.category,
                direct_dependencies_count=result.direct_dependencies_count,
                direct_internal_dependencies_count=result.direct_internal_dependencies_count,
                direct_external_dependencies_count=result.direct_external_dependencies_count,
                transitive_dependencies_count=result.transitive_dependencies_count,
                dependency_depth_analyzed=result.dependency_depth_analyzed,
                dependency_weight=result.dependency_weight,
                effective_token_size=result.effective_token_size,
                refactor_priority_score=result.refactor_priority_score,
                fan_in=result.fan_in,
                fan_out=result.fan_out,
            )
        )
    return merged


def aggregate_directories(
    file_infos: Sequence[FileTokenInfo],
    depth: int = 2,
) -> list[DirectoryTokenInfo]:
    """Aggregate file token counts by directory prefix."""
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "tokens": 0, "bytes": 0})
    for info in file_infos:
        parts = [part for part in info.path.split("/") if part]
        directory = "/".join(parts[:depth]) if parts else "."
        grouped[directory]["files"] += 1
        grouped[directory]["tokens"] += info.tokens
        grouped[directory]["bytes"] += info.bytes_

    dir_infos = [
        DirectoryTokenInfo(
            directory=directory,
            files=data["files"],
            tokens=data["tokens"],
            bytes_=data["bytes"],
        )
        for directory, data in grouped.items()
    ]
    dir_infos.sort(key=lambda item: item.tokens, reverse=True)
    return dir_infos


def build_noise_summary(
    scanner_summary: FileCollectionSummary,
    filtered_summary: FileCollectionSummary,
) -> dict[str, Any]:
    """Build scanner reduction metrics after category filtering."""
    filtered_by_category_files = scanner_summary.files - filtered_summary.files
    filtered_by_category_tokens = scanner_summary.tokens - filtered_summary.tokens

    return {
        "scanner_files": scanner_summary.files,
        "scanner_tokens": scanner_summary.tokens,
        "files_after_filters": filtered_summary.files,
        "tokens_after_filters": filtered_summary.tokens,
        "filtered_by_category_files": filtered_by_category_files,
        "filtered_by_category_tokens": filtered_by_category_tokens,
        "file_reduction_ratio": round((filtered_by_category_files / scanner_summary.files), 4)
        if scanner_summary.files
        else 0.0,
        "token_reduction_ratio": round((filtered_by_category_tokens / scanner_summary.tokens), 4)
        if scanner_summary.tokens
        else 0.0,
        "scanner_category_counts": dict(scanner_summary.category_counts),
        "scanner_category_tokens": dict(scanner_summary.category_tokens),
    }


def build_signal_score(
    category_tokens: dict[str, int],
    total_tokens: int,
) -> dict[str, Any]:
    """Estimate the analysis signal-to-noise ratio after filtering."""
    noise_tokens = category_tokens.get(FileCategory.OTHER.value, 0) + category_tokens.get(
        FileCategory.CONFIGURATION.value,
        0,
    )
    noise_ratio = (noise_tokens / total_tokens) if total_tokens else 0.0
    return {
        "value": round(max(0.0, min(100.0, (1.0 - noise_ratio) * 100.0)), 2),
        "scale": "0-100",
        "noise_tokens": noise_tokens,
        "actionable_tokens": total_tokens - noise_tokens,
        "total_tokens": total_tokens,
        "noise_ratio": round(noise_ratio, 4),
        "method": "100 * (1 - (other_tokens + configuration_tokens) / total_tokens_after_filters)",
    }


def initialize_analysis_totals(
    totals: dict[str, Any],
    *,
    analysis_scope: dict[str, Any],
    dependency_options: dict[str, Any],
    scanner_summary: FileCollectionSummary,
    filtered_summary: FileCollectionSummary,
    report_schema_version: int,
    dependency_metrics_version: int,
) -> None:
    """Populate the top-level totals envelope before dependency enrichment."""
    noise_summary = build_noise_summary(scanner_summary, filtered_summary)
    signal_score = build_signal_score(filtered_summary.category_tokens, filtered_summary.tokens)

    totals["scanner_files"] = scanner_summary.files
    totals["scanner_tokens"] = scanner_summary.tokens
    totals["files"] = filtered_summary.files
    totals["tokens"] = filtered_summary.tokens
    totals["report_schema_version"] = report_schema_version
    totals["compatibility_mode"] = "legacy"
    totals["analysis_scope"] = analysis_scope
    totals["category_counts"] = dict(filtered_summary.category_counts)
    totals["category_tokens"] = dict(filtered_summary.category_tokens)
    totals["noise_summary"] = noise_summary
    totals["signal_score"] = signal_score
    totals["dependency_analysis"] = {
        "dependency_metrics_version": dependency_metrics_version,
        "enabled": dependency_options["enabled"],
        "mode": dependency_options["mode"],
        "config_path": dependency_options["config_path"],
        "max_depth": dependency_options["max_depth"],
        "max_multiplier": dependency_options["max_multiplier"],
        "base_weight": dependency_options["base_weight"],
        "depth_decay": dependency_options["depth_decay"],
        "depth_weights": dependency_options["depth_weights"],
        "internal_dependency_weight": dependency_options["internal_dependency_weight"],
        "external_dependency_weight": dependency_options["external_dependency_weight"],
        "fan_in_weight": dependency_options["fan_in_weight"],
        "cycle_penalty": dependency_options["cycle_penalty"],
    }


def apply_dependency_analysis(
    project_path: str,
    file_infos: Sequence[FileTokenInfo],
    dependency_options: dict[str, Any],
    top_n: int,
) -> tuple[list[FileTokenInfo], dict[str, Any]]:
    """Apply dependency graph weighting and return merged file infos plus totals."""
    graph = build_dependency_graph(file_infos, project_path)
    dependency_results_list = compute_dependency_weights(
        file_infos=file_infos,
        graph=graph,
        max_depth=dependency_options["max_depth"],
        max_multiplier=dependency_options["max_multiplier"],
        base_weight=dependency_options["base_weight"],
        depth_decay=dependency_options["depth_decay"],
        depth_weights=dependency_options["depth_weights"],
        internal_dependency_weight=dependency_options["internal_dependency_weight"],
        external_dependency_weight=dependency_options["external_dependency_weight"],
        fan_in_weight=dependency_options["fan_in_weight"],
        cycle_penalty=dependency_options["cycle_penalty"],
    )
    dependency_results = {result.file_path: result for result in dependency_results_list}
    merged_file_infos = merge_dependency_metrics(file_infos, dependency_results)

    effective_tokens = sum(
        file_info.effective_token_size if file_info.effective_token_size > 0 else file_info.tokens
        for file_info in merged_file_infos
    )
    hotspots = sorted(
        (file_info for file_info in merged_file_infos if file_info.effective_token_size > 0),
        key=lambda file_info: (file_info.refactor_priority_score, file_info.effective_token_size),
        reverse=True,
    )

    return merged_file_infos, {
        "compatibility_mode": dependency_options["mode"],
        "dependency_analysis": {
            "effective_tokens": effective_tokens,
            "source_files_analyzed": graph.total_files,
            "dependency_edges": graph.total_edges,
            "cycle_groups": len(graph.cycle_groups),
            "files_with_dependency_data": len(dependency_results_list),
            "hotspots": [file_info.to_dict() for file_info in hotspots[: min(top_n, 25)]],
        },
    }
