"""Refactoring recommendation and plan model types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model_enums import CodeSmell, FileCategory, Priority, RefactorTechnique


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
            "techniques": [technique.value for technique in self.techniques],
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
            "steps": [step.to_dict() for step in self.steps],
            "total_estimated_token_reduction": self.total_estimated_token_reduction,
            "projected_tokens_after": self.projected_tokens_after,
            "fits_context_after": self.fits_context_after,
        }
