"""Domain models for ContextRefactor.

All data structures are immutable dataclasses to keep the core logic
side-effect-free and easy to serialise to JSON for the MCP layer.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


# ── Enumerations ──────────────────────────────────────────────────────────────


class FileCategory(str, enum.Enum):
    """High-level file classification used to route analysis."""

    SOURCE_CODE = "source_code"
    MARKDOWN = "markdown"
    CONFIGURATION = "configuration"
    BINARY = "binary"
    OTHER = "other"


class CodeSmell(str, enum.Enum):
    """Detectable code smells (subset of Fowler / refactoring.guru catalog)."""

    LONG_METHOD = "Long Method"
    LARGE_CLASS = "Large Class"
    LONG_PARAMETER_LIST = "Long Parameter List"
    DUPLICATE_CODE = "Duplicate Code"
    DEEP_NESTING = "Deep Nesting"
    GOD_FILE = "God File"
    MIXED_RESPONSIBILITIES = "Mixed Responsibilities"
    POOR_NAMING = "Poor Naming"


class RefactorTechnique(str, enum.Enum):
    """Refactoring techniques from https://refactoring.guru/refactoring/techniques."""

    EXTRACT_METHOD = "Extract Method"
    EXTRACT_CLASS = "Extract Class"
    MOVE_METHOD = "Move Method"
    MOVE_FIELD = "Move Field"
    RENAME_METHOD = "Rename Method"
    EXTRACT_VARIABLE = "Extract Variable"
    REPLACE_TEMP_WITH_QUERY = "Replace Temp with Query"
    DECOMPOSE_CONDITIONAL = "Decompose Conditional"
    SPLIT_DOCUMENT = "Split Document"
    EXTRACT_MODULE = "Extract Module"
    RENAME_VARIABLE = "Rename Variable"


class Priority(str, enum.Enum):
    """Priority level for refactoring recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── File / Token Info ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FileTokenInfo:
    """Token information for a single file (mirroring token_report.py output)."""

    path: str
    ext: str
    tokens: int
    bytes_: int
    chars: int
    category: FileCategory = FileCategory.OTHER

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "ext": self.ext,
            "tokens": self.tokens,
            "bytes": self.bytes_,
            "chars": self.chars,
            "category": self.category.value,
        }


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


# ── Context Budget ────────────────────────────────────────────────────────────


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


# ── Code Analysis ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FunctionInfo:
    """Basic information about a detected function / method."""

    name: str
    start_line: int
    end_line: int
    line_count: int
    parameter_count: int
    nesting_depth: int = 0


@dataclass(frozen=True)
class ClassInfo:
    """Basic information about a detected class."""

    name: str
    start_line: int
    end_line: int
    line_count: int
    method_count: int


@dataclass(frozen=True)
class MarkdownSection:
    """A heading-delimited section inside a Markdown document."""

    heading: str
    level: int
    start_line: int
    end_line: int
    line_count: int
    suggested_filename: str


# ── Refactoring Recommendations ──────────────────────────────────────────────


@dataclass(frozen=True)
class RefactorRecommendation:
    """A single actionable refactoring recommendation for a specific file."""

    file_path: str
    category: FileCategory
    smell: CodeSmell | None
    technique: RefactorTechnique
    priority: Priority
    description: str
    estimated_token_reduction: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "category": self.category.value,
            "smell": self.smell.value if self.smell else None,
            "technique": self.technique.value,
            "priority": self.priority.value,
            "description": self.description,
            "estimated_token_reduction": self.estimated_token_reduction,
            "details": self.details,
        }


# ── Refactor Plan ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RefactorStep:
    """One discrete step inside a refactoring plan."""

    step_number: int
    title: str
    description: str
    affected_files: list[str]
    techniques: list[RefactorTechnique]
    estimated_token_reduction: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "title": self.title,
            "description": self.description,
            "affected_files": self.affected_files,
            "techniques": [t.value for t in self.techniques],
            "estimated_token_reduction": self.estimated_token_reduction,
        }


@dataclass(frozen=True)
class RefactorPlan:
    """Complete, ordered refactoring plan."""

    steps: list[RefactorStep]
    total_estimated_token_reduction: int
    projected_tokens_after: int
    fits_context_after: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "total_estimated_token_reduction": self.total_estimated_token_reduction,
            "projected_tokens_after": self.projected_tokens_after,
            "fits_context_after": self.fits_context_after,
        }


# ── Top-Level Result ──────────────────────────────────────────────────────────


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
    """Per-file result produced by the HeuristicsEngine.

    Combines human-readable smell labels with structured recommendations
    suitable for planner integration.
    """

    file: str
    tokens: int
    language: str
    problems: list[str]
    suggested_refactors: list[str]
    recommendations: list[RefactorRecommendation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "tokens": self.tokens,
            "language": self.language,
            "problems": self.problems,
            "suggested_refactors": self.suggested_refactors,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


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
            "largest_files": [f.to_dict() for f in self.largest_files],
            "largest_directories": [d.to_dict() for d in self.largest_directories],
            "refactor_recommendations": [r.to_dict() for r in self.refactor_recommendations],
            "refactor_plan": self.refactor_plan.to_dict() if self.refactor_plan else None,
        }
