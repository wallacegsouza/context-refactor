"""Support helpers for the heuristics-based refactor engine."""

from __future__ import annotations

import os

from .models import Priority, RefactorRecommendation
from .refactor_rules import (
    DuplicateCodeRule,
    HighCouplingRule,
    LargeClassRule,
    LargeFileRule,
    LongMethodRule,
    RefactorRule,
)

_EXT_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".swift": "swift",
    ".scala": "scala",
    ".lua": "lua",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".md": "markdown",
    ".mdx": "markdown",
    ".rst": "restructuredtext",
}

_PRIORITY_RANK: dict[Priority, int] = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


def _priority_rank(priority: Priority) -> int:
    return _PRIORITY_RANK.get(priority, 99)


def _deduplicate(
    recommendations: list[RefactorRecommendation],
) -> list[RefactorRecommendation]:
    """Deduplicate on (file_path, smell, technique); keep highest-priority entry."""
    seen: dict[tuple[str, str | None, str], RefactorRecommendation] = {}
    for recommendation in recommendations:
        key = (
            recommendation.file_path,
            recommendation.smell.value if recommendation.smell else None,
            recommendation.technique.value,
        )
        existing = seen.get(key)
        if existing is None or _priority_rank(recommendation.priority) < _priority_rank(existing.priority):
            seen[key] = recommendation
    return list(seen.values())


def _extract_problems(recommendations: list[RefactorRecommendation]) -> list[str]:
    """Return unique human-readable smell names, preserving insertion order."""
    seen: set[str] = set()
    result: list[str] = []
    for recommendation in recommendations:
        label = recommendation.smell.value if recommendation.smell else "Unknown"
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def _short_target(recommendation: RefactorRecommendation) -> str:
    """Extract the most descriptive target name from a recommendation's details."""
    if "class" in recommendation.details:
        return str(recommendation.details["class"])
    if "function" in recommendation.details:
        return str(recommendation.details["function"])
    return os.path.basename(recommendation.file_path)


def _extract_suggestions(recommendations: list[RefactorRecommendation]) -> list[str]:
    """Build human-readable suggestion strings like 'Extract Class: UserValidator'."""
    suggestions: list[str] = []
    for recommendation in recommendations[:10]:
        suggestions.append(f"{recommendation.technique.value}: {_short_target(recommendation)}")
    return suggestions


def build_default_rules(
    context_window_size: int,
    extra_rules: list[RefactorRule] | None = None,
) -> list[RefactorRule]:
    """Build the default pluggable rules for the heuristics engine."""
    rules: list[RefactorRule] = [
        LargeFileRule(context_window_size=context_window_size),
        LongMethodRule(threshold_lines=80),
        LargeClassRule(threshold_lines=500, threshold_methods=20),
        DuplicateCodeRule(),
        HighCouplingRule(),
    ]
    if extra_rules:
        rules.extend(extra_rules)
    return rules
