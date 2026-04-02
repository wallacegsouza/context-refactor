"""Top-level result model types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .model_refactoring import RefactorPlan, RefactorRecommendation
from .model_tokens import ContextBudget, DirectoryTokenInfo, FileTokenInfo


@dataclass(frozen=True)
class ProjectSummary:
    """Top-level analysis result returned by the MCP tools."""

    files: int
    total_tokens: int
    context_budget: int
    fits_context: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": self.files,
            "total_tokens": self.total_tokens,
            "context_budget": self.context_budget,
            "fits_context": self.fits_context,
        }


@dataclass(frozen=True)
class HeuristicResult:
    """Per-file result produced by the HeuristicsEngine."""

    file: str
    tokens: int
    language: str
    problems: list[str]
    suggested_refactors: list[str]
    recommendations: list[RefactorRecommendation]
    dependency_weight: float = 1.0
    effective_token_size: int = 0
    refactor_priority_score: float = 0.0
    fan_in: int = 0
    fan_out: int = 0

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "file": self.file,
            "tokens": self.tokens,
            "language": self.language,
            "problems": self.problems,
            "suggested_refactors": self.suggested_refactors,
            "recommendations": [recommendation.to_dict() for recommendation in self.recommendations],
        }
        if self.effective_token_size > 0:
            result["dependency_weight"] = round(self.dependency_weight, 4)
            result["effective_token_size"] = self.effective_token_size
            result["refactor_priority_score"] = round(self.refactor_priority_score, 4)
            result["fan_in"] = self.fan_in
            result["fan_out"] = self.fan_out
        return result


@dataclass
class AnalysisResult:
    """Aggregated output of a full project analysis."""

    project_summary: ProjectSummary
    context_budget: ContextBudget
    largest_files: list[FileTokenInfo]
    largest_directories: list[DirectoryTokenInfo]
    refactor_recommendations: list[RefactorRecommendation]
    refactor_plan: RefactorPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_summary": self.project_summary.to_dict(),
            "context_budget": self.context_budget.to_dict(),
            "largest_files": [file_info.to_dict() for file_info in self.largest_files],
            "largest_directories": [directory.to_dict() for directory in self.largest_directories],
            "refactor_recommendations": [
                recommendation.to_dict()
                for recommendation in self.refactor_recommendations
            ],
            "refactor_plan": self.refactor_plan.to_dict() if self.refactor_plan else None,
        }
