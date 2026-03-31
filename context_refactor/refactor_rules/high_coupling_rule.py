"""HighCouplingRule — flags files with high dependency surface and blast radius."""

from __future__ import annotations

import os

from ..models import (
    CodeSmell,
    FileCategory,
    FileTokenInfo,
    Priority,
    RefactorRecommendation,
    RefactorTechnique,
)
from .base import RefactorRule


class HighCouplingRule(RefactorRule):
    """Flag files whose dependency surface suggests hard-to-isolate refactors."""

    def __init__(
        self,
        min_dependency_weight: float = 1.75,
        min_direct_dependencies: int = 6,
        min_transitive_dependencies: int = 12,
        min_fan_out: int = 6,
    ) -> None:
        self._min_dependency_weight = min_dependency_weight
        self._min_direct_dependencies = min_direct_dependencies
        self._min_transitive_dependencies = min_transitive_dependencies
        self._min_fan_out = min_fan_out

    def applies_to(self, file_info: FileTokenInfo) -> bool:
        return (
            file_info.category == FileCategory.SOURCE_CODE
            and file_info.effective_token_size > 0
        )

    def evaluate(
        self,
        file_info: FileTokenInfo,
        project_path: str,
    ) -> list[RefactorRecommendation]:
        if (
            file_info.dependency_weight < self._min_dependency_weight
            and file_info.direct_dependencies_count < self._min_direct_dependencies
            and file_info.transitive_dependencies_count < self._min_transitive_dependencies
            and file_info.fan_out < self._min_fan_out
        ):
            return []

        abs_path = os.path.join(project_path, file_info.path)
        priority = (
            Priority.HIGH
            if file_info.refactor_priority_score >= 0.85 or file_info.fan_out >= self._min_fan_out * 2
            else Priority.MEDIUM
        )

        return [
            RefactorRecommendation(
                file_path=abs_path,
                category=FileCategory.SOURCE_CODE,
                smell=CodeSmell.HIGH_COUPLING,
                technique=RefactorTechnique.INVERT_DEPENDENCY,
                priority=priority,
                description=(
                    "File has high dependency surface: "
                    f"{file_info.direct_dependencies_count} direct deps, "
                    f"{file_info.transitive_dependencies_count} transitive deps, "
                    f"fan_out={file_info.fan_out}, "
                    f"weight={file_info.dependency_weight:.2f}. "
                    "Reduce coupling before deeper structural refactors."
                ),
                estimated_token_reduction=int(
                    max(file_info.tokens, file_info.effective_token_size) * 0.08
                ),
                details={
                    "direct_dependencies_count": file_info.direct_dependencies_count,
                    "transitive_dependencies_count": file_info.transitive_dependencies_count,
                    "fan_in": file_info.fan_in,
                    "fan_out": file_info.fan_out,
                    "dependency_weight": round(file_info.dependency_weight, 4),
                    "effective_token_size": file_info.effective_token_size,
                    "refactor_priority_score": round(file_info.refactor_priority_score, 4),
                },
            )
        ]
