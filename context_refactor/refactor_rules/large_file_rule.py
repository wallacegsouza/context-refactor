"""LargeFileRule — flags files that exceed a context-window-relative token threshold."""

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


class LargeFileRule(RefactorRule):
    """Flag files whose token count exceeds *threshold_pct* of the context window.

    Unlike the hard-coded ``GOD_FILE_TOKENS`` in ``code_refactor.py``, this
    rule scales with the actual LLM context size so that the threshold is
    always relative to the window being targeted.

    Parameters
    ----------
    context_window_size:
        Total context window in tokens (e.g. 128 000 for Claude Sonnet).
    threshold_pct:
        Fraction of the context window that a single file must not exceed.
        Default is 0.15 (15 %).
    """

    def __init__(
        self,
        context_window_size: int = 128_000,
        threshold_pct: float = 0.15,
    ) -> None:
        self._threshold = max(1, int(context_window_size * threshold_pct))
        self._context_window_size = context_window_size
        self._threshold_pct = threshold_pct

    # ------------------------------------------------------------------

    def applies_to(self, file_info: FileTokenInfo) -> bool:
        return file_info.category in {FileCategory.SOURCE_CODE, FileCategory.MARKDOWN}

    def evaluate(
        self,
        file_info: FileTokenInfo,
        project_path: str,
    ) -> list[RefactorRecommendation]:
        if file_info.tokens < self._threshold:
            return []

        pct_of_window = (file_info.tokens / self._context_window_size) * 100
        priority = (
            Priority.CRITICAL
            if file_info.tokens >= self._threshold * 2
            else Priority.HIGH
        )

        return [
            RefactorRecommendation(
                file_path=os.path.join(project_path, file_info.path),
                category=file_info.category,
                smell=CodeSmell.GOD_FILE,
                technique=RefactorTechnique.EXTRACT_MODULE,
                priority=priority,
                description=(
                    f"File uses ~{pct_of_window:.1f}% of the context window "
                    f"({file_info.tokens:,} tokens).  "
                    f"Threshold is {self._threshold_pct:.0%} = {self._threshold:,} tokens.  "
                    f"Decompose into smaller, focused modules."
                ),
                estimated_token_reduction=int(file_info.tokens * 0.30),
                details={
                    "tokens": file_info.tokens,
                    "threshold": self._threshold,
                    "pct_of_window": round(pct_of_window, 1),
                    "context_window_size": self._context_window_size,
                },
            )
        ]
