"""Heuristics engine implementation."""

from __future__ import annotations

import os
from collections.abc import Sequence

from .code_refactor import analyze_source_file
from .models import (
    ContextBudget,
    FileCategory,
    FileTokenInfo,
    HeuristicResult,
    RefactorPlan,
    RefactorRecommendation,
)
from .refactor_heuristics_support import (
    _EXT_TO_LANGUAGE,
    _deduplicate,
    _extract_problems,
    _extract_suggestions,
    _priority_rank,
    build_default_rules,
)
from .refactor_planner import generate_refactor_plan
from .refactor_rules import RefactorRule


class HeuristicsEngine:
    """Orchestrates pluggable refactor rules plus the structural analyzer."""

    def __init__(
        self,
        context_window_size: int = 128_000,
        extra_rules: list[RefactorRule] | None = None,
        rank_by_dependency: bool = False,
    ) -> None:
        self._context_window_size = context_window_size
        self._rank_by_dependency = rank_by_dependency
        self._rules = build_default_rules(context_window_size, extra_rules=extra_rules)

    def analyze_file(
        self,
        file_info: FileTokenInfo,
        project_path: str,
    ) -> HeuristicResult:
        """Run all applicable rules on a single file."""
        abs_path = os.path.join(project_path, file_info.path)
        language = _EXT_TO_LANGUAGE.get(file_info.ext.lower(), "unknown")

        recommendations: list[RefactorRecommendation] = []
        for rule in self._rules:
            if rule.applies_to(file_info):
                recommendations.extend(rule.evaluate(file_info, project_path))

        if file_info.category == FileCategory.SOURCE_CODE and os.path.isfile(abs_path):
            recommendations.extend(analyze_source_file(abs_path, file_info.tokens))

        recommendations = _deduplicate(recommendations)
        recommendations.sort(
            key=lambda recommendation: (
                _priority_rank(recommendation.priority),
                -recommendation.estimated_token_reduction,
            )
        )

        return HeuristicResult(
            file=abs_path,
            tokens=file_info.tokens,
            language=language,
            problems=_extract_problems(recommendations),
            suggested_refactors=_extract_suggestions(recommendations),
            recommendations=recommendations,
            dependency_weight=file_info.dependency_weight,
            effective_token_size=file_info.effective_token_size,
            refactor_priority_score=file_info.refactor_priority_score,
            fan_in=file_info.fan_in,
            fan_out=file_info.fan_out,
        )

    def analyze_project(
        self,
        file_infos: Sequence[FileTokenInfo],
        project_path: str,
    ) -> list[HeuristicResult]:
        """Analyze all eligible files in the project."""
        results: list[HeuristicResult] = []
        for file_info in file_infos:
            if file_info.category in {FileCategory.BINARY, FileCategory.CONFIGURATION}:
                continue
            result = self.analyze_file(file_info, project_path)
            if result.recommendations:
                results.append(result)

        if self._rank_by_dependency:
            results.sort(
                key=lambda result: (
                    result.refactor_priority_score,
                    result.effective_token_size,
                    result.tokens,
                ),
                reverse=True,
            )
        else:
            results.sort(key=lambda result: result.tokens, reverse=True)
        return results

    def generate_plan(
        self,
        results: list[HeuristicResult],
        budget: ContextBudget,
    ) -> RefactorPlan:
        """Flatten all recommendations from *results* into a planner output."""
        all_recommendations: list[RefactorRecommendation] = []
        for heuristic_result in results:
            all_recommendations.extend(heuristic_result.recommendations)
        return generate_refactor_plan(all_recommendations, budget)
