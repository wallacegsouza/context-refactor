"""LargeClassRule — flags classes that exceed a configurable size threshold."""

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


class LargeClassRule(RefactorRule):
    """Flag classes that violate the Single Responsibility Principle by sheer size.

    A class is considered large when it exceeds *threshold_lines* **or**
    contains at least *threshold_methods* methods.  Both conditions are
    checked so that a class with many small methods is also flagged even
    if its total line count is moderate.

    Parameters
    ----------
    threshold_lines:
        Line count at-or-above which a class is flagged.  Default 500
        (per the spec; ``code_refactor.py`` uses 300).
    threshold_methods:
        Method count at-or-above which a class is flagged.  Default 20.
    """

    def __init__(
        self,
        threshold_lines: int = 500,
        threshold_methods: int = 20,
    ) -> None:
        self._line_threshold = threshold_lines
        self._method_threshold = threshold_methods

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
            _, classes = _analyze_python(abs_path, source)
        else:
            lines = source.splitlines()
            _, classes = _analyze_generic(abs_path, source, ext)

        recommendations: list[RefactorRecommendation] = []
        for cls in classes:
            too_long = cls.line_count >= self._line_threshold
            too_many_methods = cls.method_count >= self._method_threshold
            if not (too_long or too_many_methods):
                continue

            reasons: list[str] = []
            if too_long:
                reasons.append(f"{cls.line_count} lines (threshold: {self._line_threshold})")
            if too_many_methods:
                reasons.append(f"{cls.method_count} methods (threshold: {self._method_threshold})")

            recommendations.append(
                RefactorRecommendation(
                    file_path=abs_path,
                    category=FileCategory.SOURCE_CODE,
                    smell=CodeSmell.LARGE_CLASS,
                    technique=RefactorTechnique.EXTRACT_CLASS,
                    priority=Priority.HIGH,
                    description=(
                        f"Class `{cls.name}` is too large: "
                        + "; ".join(reasons)
                        + ".  Split into smaller, focused classes."
                    ),
                    estimated_token_reduction=int(cls.line_count * 0.6),
                    details={
                        "class": cls.name,
                        "lines": cls.line_count,
                        "methods": cls.method_count,
                        "start_line": cls.start_line,
                        "end_line": cls.end_line,
                    },
                )
            )
        return recommendations
