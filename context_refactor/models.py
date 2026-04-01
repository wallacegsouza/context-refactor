"""Compatibility facade for ContextRefactor domain models."""

from __future__ import annotations

from .model_analysis import ClassInfo, FunctionInfo, MarkdownSection
from .model_dependencies import (
    DependencyEdge,
    DependencyGraph,
    DependencyWeightResult,
    FileDependencyInfo,
)
from .model_enums import (
    CodeSmell,
    DependencyKind,
    DependencyScope,
    FileCategory,
    Priority,
    RefactorTechnique,
)
from .model_refactoring import RefactorPlan, RefactorRecommendation, RefactorStep
from .model_results import AnalysisResult, HeuristicResult, ProjectSummary
from .model_tokens import ContextBudget, DirectoryTokenInfo, FileTokenInfo

__all__ = [
    "AnalysisResult",
    "ClassInfo",
    "CodeSmell",
    "ContextBudget",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyKind",
    "DependencyScope",
    "DependencyWeightResult",
    "DirectoryTokenInfo",
    "FileCategory",
    "FileDependencyInfo",
    "FileTokenInfo",
    "FunctionInfo",
    "HeuristicResult",
    "MarkdownSection",
    "Priority",
    "ProjectSummary",
    "RefactorPlan",
    "RefactorRecommendation",
    "RefactorStep",
    "RefactorTechnique",
]
