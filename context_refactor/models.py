"""Domain models for ContextRefactor.

All data structures are immutable dataclasses to keep the core logic
side-effect-free and easy to serialise to JSON for the MCP layer.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

# ── Enumerations ──────────────────────────────────────────────────────────────


class FileCategory(enum.StrEnum):
    """High-level file classification used to route analysis."""

    SOURCE_CODE = "source_code"
    MARKDOWN = "markdown"
    CONFIGURATION = "configuration"
    BINARY = "binary"
    OTHER = "other"


class CodeSmell(enum.StrEnum):
    """Detectable code smells (subset of Fowler / refactoring.guru catalog)."""

    LONG_METHOD = "Long Method"
    LARGE_CLASS = "Large Class"
    LONG_PARAMETER_LIST = "Long Parameter List"
    DUPLICATE_CODE = "Duplicate Code"
    DEEP_NESTING = "Deep Nesting"
    GOD_FILE = "God File"
    MIXED_RESPONSIBILITIES = "Mixed Responsibilities"
    POOR_NAMING = "Poor Naming"
    HIGH_COUPLING = "High Coupling"


class RefactorTechnique(enum.StrEnum):
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
    INVERT_DEPENDENCY = "Invert Dependency"
    INTRODUCE_INTERFACE = "Introduce Interface"


class Priority(enum.StrEnum):
    """Priority level for refactoring recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DependencyKind(enum.StrEnum):
    """Classification of a dependency relationship."""

    IMPORT = "import"
    INHERITANCE = "inheritance"
    COMPOSITION = "composition"
    TYPE_USAGE = "type_usage"
    DECORATOR = "decorator"


class DependencyScope(enum.StrEnum):
    """Whether a dependency is internal to the project or external."""

    INTERNAL = "internal"
    EXTERNAL = "external"


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


# ── Dependency Analysis ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class DependencyEdge:
    """A single dependency relationship from source to target."""

    source_file: str
    target_module: str
    target_file: str | None  # None if external
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
            "cycle_groups": [sorted(g) for g in self.cycle_groups],
            "files": {
                path: info.to_dict()
                for path, info in self.file_infos.items()
            },
        }


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
    # Dependency analysis fields (backward-compatible defaults)
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
            "recommendations": [r.to_dict() for r in self.recommendations],
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
            "largest_files": [f.to_dict() for f in self.largest_files],
            "largest_directories": [d.to_dict() for d in self.largest_directories],
            "refactor_recommendations": [r.to_dict() for r in self.refactor_recommendations],
            "refactor_plan": self.refactor_plan.to_dict() if self.refactor_plan else None,
        }
