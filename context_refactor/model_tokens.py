"""Token, directory, and context-budget model types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model_enums import FileCategory


@dataclass(frozen=True)
class FileTokenInfo:
    """Token information for a single file (mirroring token_report.py output)."""

    path: str
    ext: str
    tokens: int
    bytes_: int
    chars: int
    category: FileCategory = FileCategory.OTHER
    direct_dependencies_count: int = 0
    direct_internal_dependencies_count: int = 0
    direct_external_dependencies_count: int = 0
    transitive_dependencies_count: int = 0
    dependency_depth_analyzed: int = 0
    dependency_weight: float = 1.0
    effective_token_size: int = 0
    refactor_priority_score: float = 0.0
    fan_in: int = 0
    fan_out: int = 0

    def to_dict(self) -> dict[str, Any]:
        result = {
            "path": self.path,
            "ext": self.ext,
            "tokens": self.tokens,
            "bytes": self.bytes_,
            "chars": self.chars,
            "category": self.category.value,
        }
        if self.effective_token_size > 0:
            result["direct_dependencies_count"] = self.direct_dependencies_count
            result["direct_internal_dependencies_count"] = self.direct_internal_dependencies_count
            result["direct_external_dependencies_count"] = self.direct_external_dependencies_count
            result["transitive_dependencies_count"] = self.transitive_dependencies_count
            result["dependency_depth_analyzed"] = self.dependency_depth_analyzed
            result["dependency_weight"] = round(self.dependency_weight, 4)
            result["effective_token_size"] = self.effective_token_size
            result["refactor_priority_score"] = round(self.refactor_priority_score, 4)
            result["fan_in"] = self.fan_in
            result["fan_out"] = self.fan_out
        return result


@dataclass(frozen=True)
class DirectoryTokenInfo:
    """Aggregated token information for a directory."""

    directory: str
    files: int
    tokens: int
    bytes_: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "directory": self.directory,
            "files": self.files,
            "tokens": self.tokens,
            "bytes": self.bytes_,
        }


@dataclass(frozen=True)
class ContextBudget:
    """Result of a context-budget computation."""

    llm_context_size: int
    safety_margin: float
    context_budget: int
    total_tokens: int
    total_files: int
    fits_context: bool
    overflow_tokens: int
    overflow_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "llm_context_size": self.llm_context_size,
            "safety_margin": self.safety_margin,
            "context_budget": self.context_budget,
            "total_tokens": self.total_tokens,
            "total_files": self.total_files,
            "fits_context": self.fits_context,
            "overflow_tokens": self.overflow_tokens,
            "overflow_ratio": round(self.overflow_ratio, 4),
        }
