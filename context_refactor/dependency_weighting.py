"""Dependency weight computation helpers."""

from __future__ import annotations

import math
from collections.abc import Sequence

from .models import (
    DependencyGraph,
    DependencyWeightResult,
    FileCategory,
    FileTokenInfo,
)


def compute_dependency_weights(
    file_infos: Sequence[FileTokenInfo],
    graph: DependencyGraph,
    max_depth: int = 3,
    max_multiplier: float = 5.0,
    base_weight: float = 1.0,
    depth_decay: float = 0.5,
    depth_weights: Sequence[float] | None = None,
    internal_dependency_weight: float = 1.0,
    external_dependency_weight: float = 0.7,
    fan_in_weight: float = 0.15,
    cycle_penalty: float = 0.10,
) -> list[DependencyWeightResult]:
    """Compute dependency weight for each source file."""
    results: list[DependencyWeightResult] = []
    cycle_nodes = {node for group in graph.cycle_groups for node in group}

    for file_info in file_infos:
        if file_info.category != FileCategory.SOURCE_CODE:
            continue

        dep_info = graph.file_infos.get(file_info.path)
        if dep_info is None:
            results.append(
                DependencyWeightResult(
                    file_path=file_info.path,
                    tokens=file_info.tokens,
                    direct_dependencies_count=0,
                    direct_internal_dependencies_count=0,
                    direct_external_dependencies_count=0,
                    transitive_dependencies_count=0,
                    dependency_depth_analyzed=max_depth,
                    fan_in=0,
                    fan_out=0,
                    dependency_weight=base_weight,
                    effective_token_size=file_info.tokens,
                    refactor_priority_score=0.0,
                )
            )
            continue

        level_counts = _count_dependencies_by_level(file_info.path, graph.adjacency, max_depth)
        direct_internal_count = level_counts[0] if level_counts else 0
        direct_external_count = dep_info.external_dependency_count
        direct_count = direct_internal_count + direct_external_count
        transitive_count = sum(level_counts[1:]) if len(level_counts) > 1 else 0

        raw_weight = (direct_external_count * external_dependency_weight) + sum(
            count
            * internal_dependency_weight
            * _level_weight(level, depth_weights=depth_weights, depth_decay=depth_decay)
            for level, count in enumerate(level_counts)
        )

        dampened = math.sqrt(raw_weight) if raw_weight > 0 else 0.0
        multiplier = min(base_weight + dampened, max_multiplier)
        effective = math.floor(file_info.tokens * multiplier)

        results.append(
            DependencyWeightResult(
                file_path=file_info.path,
                tokens=file_info.tokens,
                direct_dependencies_count=direct_count,
                direct_internal_dependencies_count=direct_internal_count,
                direct_external_dependencies_count=direct_external_count,
                transitive_dependencies_count=transitive_count,
                dependency_depth_analyzed=max_depth,
                fan_in=dep_info.fan_in,
                fan_out=dep_info.fan_out,
                dependency_weight=multiplier,
                effective_token_size=effective,
                refactor_priority_score=0.0,
            )
        )

    return _normalize_priority_scores(results, cycle_nodes, fan_in_weight, cycle_penalty)


def _count_dependencies_by_level(
    file_path: str,
    adjacency: dict[str, set[str]],
    max_depth: int,
) -> list[int]:
    """BFS to count dependencies at each depth level."""
    counts: list[int] = []
    visited: set[str] = {file_path}
    current_level: set[str] = {file_path}

    for _ in range(max_depth):
        next_level: set[str] = set()
        for node in current_level:
            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_level.add(neighbor)
        counts.append(len(next_level))
        current_level = next_level
        if not current_level:
            break

    while len(counts) < max_depth:
        counts.append(0)

    return counts


def _level_weight(
    level_index: int,
    *,
    depth_weights: Sequence[float] | None,
    depth_decay: float,
) -> float:
    if depth_weights:
        if level_index < len(depth_weights):
            return float(depth_weights[level_index])
        return float(depth_weights[-1])
    return depth_decay ** level_index


def _normalize_priority_scores(
    results: list[DependencyWeightResult],
    cycle_nodes: set[str],
    fan_in_weight: float,
    cycle_penalty: float,
) -> list[DependencyWeightResult]:
    if not results:
        return results

    max_effective = max(result.effective_token_size for result in results)
    max_fan_in = max(result.fan_in for result in results)
    if max_effective <= 0:
        return results

    normalized: list[DependencyWeightResult] = []
    for result in results:
        normalized.append(
            DependencyWeightResult(
                file_path=result.file_path,
                tokens=result.tokens,
                direct_dependencies_count=result.direct_dependencies_count,
                direct_internal_dependencies_count=result.direct_internal_dependencies_count,
                direct_external_dependencies_count=result.direct_external_dependencies_count,
                transitive_dependencies_count=result.transitive_dependencies_count,
                dependency_depth_analyzed=result.dependency_depth_analyzed,
                fan_in=result.fan_in,
                fan_out=result.fan_out,
                dependency_weight=result.dependency_weight,
                effective_token_size=result.effective_token_size,
                refactor_priority_score=min(
                    1.0,
                    (result.effective_token_size / max_effective)
                    + (((result.fan_in / max_fan_in) * fan_in_weight) if max_fan_in > 0 else 0.0)
                    + (cycle_penalty if result.file_path in cycle_nodes else 0.0),
                ),
            )
        )

    return normalized
