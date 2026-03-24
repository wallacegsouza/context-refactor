"""LongMethodRule — flags functions/methods that exceed a configurable line threshold."""

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
from ..code_refactor import _analyze_python, _analyze_generic  # type: ignore[attr-defined]
from .base import RefactorRule


class LongMethodRule(RefactorRule):
    """Flag functions whose body exceeds *threshold_lines* lines.

    Uses the same AST-based (Python) and regex-based (other languages)
    parsers as ``code_refactor.analyze_source_file`` — but with a
    higher configurable threshold (default 80 lines vs. the existing 60).

    Parameters
    ----------
    threshold_lines:
        Number of lines at-or-above which a function is flagged.
        Default 80 (per the spec).
    """

    def __init__(self, threshold_lines: int = 80) -> None:
        self._threshold = threshold_lines

    # ------------------------------------------------------------------

    def applies_to(self, file_info: FileTokenInfo) -> bool:
        return file_info.category == FileCategory.SOURCE_CODE

    def evaluate(
        self,
        file_info: FileTokenInfo,
        project_path: str,
    ) -> list[RefactorRecommendation]:
        abs_path = os.path.join(project_path, file_info.path)
        if not os.path.isfile(abs_path):
            return []

        try:
            with open(abs_path, encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
        except OSError:
            return []

        ext = file_info.ext.lower()
        if ext == ".py":
            funcs, _ = _analyze_python(abs_path, source)
        else:
            lines = source.splitlines()
            funcs, _ = _analyze_generic(abs_path, source, ext)

        recommendations: list[RefactorRecommendation] = []
        for fn in funcs:
            if fn.line_count < self._threshold:
                continue
            priority = (
                Priority.HIGH
                if fn.line_count >= self._threshold * 2
                else Priority.MEDIUM
            )
            recommendations.append(
                RefactorRecommendation(
                    file_path=abs_path,
                    category=FileCategory.SOURCE_CODE,
                    smell=CodeSmell.LONG_METHOD,
                    technique=RefactorTechnique.EXTRACT_METHOD,
                    priority=priority,
                    description=(
                        f"Function `{fn.name}` has {fn.line_count} lines "
                        f"(threshold: {self._threshold}).  "
                        f"Extract smaller, cohesive helper methods."
                    ),
                    estimated_token_reduction=int(fn.line_count * 0.8),
                    details={
                        "function": fn.name,
                        "lines": fn.line_count,
                        "start_line": fn.start_line,
                        "end_line": fn.end_line,
                    },
                )
            )
        return recommendations
