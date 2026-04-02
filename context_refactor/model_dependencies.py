"""Dependency-analysis model types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model_enums import DependencyKind, DependencyScope


@dataclass(frozen=True)
class DependencyEdge:
    """A single dependency relationship from source to target."""

    source_file: str
    target_module: str
    target_file: str | None
    kind: DependencyKind
    scope: DependencyScope
    symbol: str
    line_number: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "target_module": self.target_module,
            "target_file": self.target_file,
            "kind": self.kind.value,
            "scope": self.scope.value,
            "symbol": self.symbol,
            "line_number": self.line_number,
        }


@dataclass(frozen=True)
class FileDependencyInfo:
    """Aggregated dependency metrics for a single file."""

    file_path: str
    direct_dependencies: list[DependencyEdge]
    direct_dependents: list[DependencyEdge]
    fan_out: int
    fan_in: int
    internal_dependency_count: int
    external_dependency_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "fan_out": self.fan_out,
            "fan_in": self.fan_in,
            "internal_dependencies": self.internal_dependency_count,
            "external_dependencies": self.external_dependency_count,
            "direct_dependencies_count": len(self.direct_dependencies),
            "direct_dependents_count": len(self.direct_dependents),
        }


@dataclass(frozen=True)
class DependencyWeightResult:
    """Computed dependency weight for a file, combining token size with coupling."""

    file_path: str
    tokens: int
    direct_dependencies_count: int
    direct_internal_dependencies_count: int
    direct_external_dependencies_count: int
    transitive_dependencies_count: int
    dependency_depth_analyzed: int
    fan_in: int
    fan_out: int
    dependency_weight: float
    effective_token_size: int
    refactor_priority_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "tokens": self.tokens,
            "direct_dependencies_count": self.direct_dependencies_count,
            "direct_internal_dependencies_count": self.direct_internal_dependencies_count,
            "direct_external_dependencies_count": self.direct_external_dependencies_count,
            "transitive_dependencies_count": self.transitive_dependencies_count,
            "dependency_depth_analyzed": self.dependency_depth_analyzed,
            "fan_in": self.fan_in,
            "fan_out": self.fan_out,
            "dependency_weight": round(self.dependency_weight, 4),
            "effective_token_size": self.effective_token_size,
            "refactor_priority_score": round(self.refactor_priority_score, 4),
        }


@dataclass
class DependencyGraph:
    """Project-wide dependency graph built from import analysis."""

    edges: list[DependencyEdge]
    file_infos: dict[str, FileDependencyInfo]
    adjacency: dict[str, set[str]]
    reverse_adjacency: dict[str, set[str]]
    cycle_groups: list[set[str]]
    total_files: int
    total_edges: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "total_edges": self.total_edges,
            "cycle_groups_count": len(self.cycle_groups),
            "cycle_groups": [sorted(group) for group in self.cycle_groups],
            "files": {
                path: info.to_dict()
                for path, info in self.file_infos.items()
            },
        }
