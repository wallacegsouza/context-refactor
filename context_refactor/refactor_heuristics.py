"""Refactor Heuristics Engine — orchestrates pluggable rules and produces per-file results.

This module is the central entry point for the heuristics-based analysis.
It differs from :mod:`refactor_engine` in that:

* Rules are *classes* (implementing :class:`~refactor_rules.base.RefactorRule`)
  rather than ad-hoc inline conditionals.
* The large-file threshold is **context-window-relative** (15 % by default)
  rather than hard-coded.
* Results are grouped *per file* into :class:`~models.HeuristicResult` objects
  that contain both human-readable strings and structured
  :class:`~models.RefactorRecommendation` instances.
* A :meth:`HeuristicsEngine.generate_plan` convenience method ties the engine
  directly to the existing :func:`~refactor_planner.generate_refactor_plan`
  planner.

Usage example::

    from context_refactor.refactor_heuristics import HeuristicsEngine
    from context_refactor.analyzer import analyze_tokens
    from context_refactor.context_budget import compute_budget

    file_infos, _, totals = analyze_tokens("/path/to/project")
    budget = compute_budget(totals["tokens"], totals["files"])

    engine = HeuristicsEngine(context_window_size=128_000)
    results = engine.analyze_project(file_infos, "/path/to/project")
    plan    = engine.generate_plan(results, budget)
"""

from __future__ import annotations

import os
from collections.abc import Sequence

from .code_refactor import analyze_source_file
from .models import (
    ContextBudget,
    FileCategory,
    FileTokenInfo,
    HeuristicResult,
    Priority,
    RefactorPlan,
    RefactorRecommendation,
)
from .refactor_planner import generate_refactor_plan
from .refactor_rules import (
    DuplicateCodeRule,
    LargeClassRule,
    LargeFileRule,
    LongMethodRule,
    RefactorRule,
)

# ── Language detection ────────────────────────────────────────────────────────

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

# ── Priority ranking (lower = higher priority) ────────────────────────────────

_PRIORITY_RANK: dict[Priority, int] = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}


# ── Private helpers ───────────────────────────────────────────────────────────


def _priority_rank(p: Priority) -> int:
    return _PRIORITY_RANK.get(p, 99)


def _deduplicate(
    recs: list[RefactorRecommendation],
) -> list[RefactorRecommendation]:
    """Deduplicate on (file_path, smell, technique); keep highest-priority entry."""
    seen: dict[tuple[str, str | None, str], RefactorRecommendation] = {}
    for rec in recs:
        key = (
            rec.file_path,
            rec.smell.value if rec.smell else None,
            rec.technique.value,
        )
        existing = seen.get(key)
        if existing is None or _priority_rank(rec.priority) < _priority_rank(existing.priority):
            seen[key] = rec
    return list(seen.values())


def _extract_problems(recs: list[RefactorRecommendation]) -> list[str]:
    """Return unique human-readable smell names, preserving insertion order."""
    seen: set[str] = set()
    result: list[str] = []
    for r in recs:
        label = r.smell.value if r.smell else "Unknown"
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def _short_target(rec: RefactorRecommendation) -> str:
    """Extract the most descriptive target name from a recommendation's details."""
    if "class" in rec.details:
        return str(rec.details["class"])
    if "function" in rec.details:
        return str(rec.details["function"])
    return os.path.basename(rec.file_path)


def _extract_suggestions(recs: list[RefactorRecommendation]) -> list[str]:
    """Build human-readable suggestion strings like 'Extract Class: UserValidator'."""
    suggestions: list[str] = []
    for r in recs[:10]:  # Cap to keep output readable
        suggestions.append(f"{r.technique.value}: {_short_target(r)}")
    return suggestions


# ══════════════════════════════════════════════════════════════════════════════
# HeuristicsEngine
# ══════════════════════════════════════════════════════════════════════════════


class HeuristicsEngine:
    """Orchestrates pluggable :class:`~refactor_rules.base.RefactorRule` instances.

    The engine runs both:

    1. The **new pluggable rules** (e.g. :class:`~refactor_rules.LargeFileRule`)
       which use context-window-relative thresholds and higher line limits.
    2. The **existing structural analyzer** (:func:`~code_refactor.analyze_source_file`)
       which covers Long Parameter List, Deep Nesting, and lower-threshold smells.

    Results from both sources are deduplicated so that the same smell is not
    reported twice for the same file/function/technique triple.

    Parameters
    ----------
    context_window_size:
        Target LLM context window in tokens.  Used by :class:`LargeFileRule`
        to compute the 15 % threshold.
    extra_rules:
        Additional :class:`~refactor_rules.base.RefactorRule` instances to
        append to the default rule set.  Use this for custom project-specific
        heuristics without modifying this module.
    """

    def __init__(
        self,
        context_window_size: int = 128_000,
        extra_rules: list[RefactorRule] | None = None,
    ) -> None:
        self._context_window_size = context_window_size
        self._rules: list[RefactorRule] = [
            LargeFileRule(context_window_size=context_window_size),
            LongMethodRule(threshold_lines=80),
            LargeClassRule(threshold_lines=500, threshold_methods=20),
            DuplicateCodeRule(),
        ]
        if extra_rules:
            self._rules.extend(extra_rules)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_file(
        self,
        file_info: FileTokenInfo,
        project_path: str,
    ) -> HeuristicResult:
        """Run all applicable rules on a single file.

        Parameters
        ----------
        file_info:
            Token-annotated metadata produced by :func:`~analyzer.analyze_tokens`.
        project_path:
            Absolute path to the project root.

        Returns
        -------
        HeuristicResult
            Per-file result with human-readable problems, suggestions, and
            structured recommendations suitable for planner integration.
        """
        abs_path = os.path.join(project_path, file_info.path)
        ext = file_info.ext.lower()
        language = _EXT_TO_LANGUAGE.get(ext, "unknown")

        # 1. Pluggable rules
        recommendations: list[RefactorRecommendation] = []
        for rule in self._rules:
            if rule.applies_to(file_info):
                recommendations.extend(rule.evaluate(file_info, project_path))

        # 2. Existing structural analyzer (covers LongParameterList, DeepNesting, etc.)
        if file_info.category == FileCategory.SOURCE_CODE and os.path.isfile(abs_path):
            recommendations.extend(analyze_source_file(abs_path, file_info.tokens))

        # 3. Deduplicate
        recommendations = _deduplicate(recommendations)

        # 4. Sort by priority then estimated reduction
        recommendations.sort(
            key=lambda r: (_priority_rank(r.priority), -r.estimated_token_reduction)
        )

        return HeuristicResult(
            file=abs_path,
            tokens=file_info.tokens,
            language=language,
            problems=_extract_problems(recommendations),
            suggested_refactors=_extract_suggestions(recommendations),
            recommendations=recommendations,
        )

    def analyze_project(
        self,
        file_infos: Sequence[FileTokenInfo],
        project_path: str,
    ) -> list[HeuristicResult]:
        """Analyze all eligible files in the project.

        Binary and configuration files are skipped.  Only files that
        produce at least one recommendation are included in the result.

        Returns
        -------
        list[HeuristicResult]
            Results sorted by token count descending (highest-impact files first).
        """
        results: list[HeuristicResult] = []
        for fi in file_infos:
            if fi.category in {FileCategory.BINARY, FileCategory.CONFIGURATION}:
                continue
            result = self.analyze_file(fi, project_path)
            if result.recommendations:
                results.append(result)

        results.sort(key=lambda r: r.tokens, reverse=True)
        return results

    def generate_plan(
        self,
        results: list[HeuristicResult],
        budget: ContextBudget,
    ) -> RefactorPlan:
        """Flatten all recommendations from *results* into a :class:`~models.RefactorPlan`.

        Delegates to the existing :func:`~refactor_planner.generate_refactor_plan`
        planner so that plan-generation logic remains centralised.

        Parameters
        ----------
        results:
            Output of :meth:`analyze_project`.
        budget:
            Context budget; used to project post-refactor token fit.

        Returns
        -------
        RefactorPlan
        """
        all_recs: list[RefactorRecommendation] = []
        for hr in results:
            all_recs.extend(hr.recommendations)
        return generate_refactor_plan(all_recs, budget)
