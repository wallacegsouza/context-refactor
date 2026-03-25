"""DuplicateCodeRule — detects repeated consecutive-line groups within a file."""

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

# Sliding-window size (consecutive non-blank normalized lines).
_WINDOW: int = 5

# Minimum number of times a group must appear to be flagged.
_MIN_OCCURRENCES: int = 3

# Minimum normalized-line count before bothering (fast-exit guard).
_MIN_LINES: int = _WINDOW * _MIN_OCCURRENCES  # 15


class DuplicateCodeRule(RefactorRule):
    """Flag files that contain repeated blocks of consecutive lines.

    Algorithm
    ---------
    1. Read the file and strip each line (skip blank lines).
    2. Build a sliding window of :data:`_WINDOW` consecutive normalized lines.
    3. Count occurrences of each window (dict key = joined string).
    4. If any window appears :data:`_MIN_OCCURRENCES` or more times, emit a
       recommendation to extract the repeated logic into a shared helper.

    The approach runs in O(n) time where n = number of non-blank lines and
    is intentionally conservative (no cross-file analysis).
    """

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
                raw_lines = fh.readlines()
        except OSError:
            return []

        normalized = [ln.strip() for ln in raw_lines if ln.strip()]

        if len(normalized) < _MIN_LINES:
            return []  # Not enough lines — fast exit

        counts: dict[str, int] = {}
        for i in range(len(normalized) - _WINDOW + 1):
            key = "\n".join(normalized[i : i + _WINDOW])
            counts[key] = counts.get(key, 0) + 1

        duplicates = {k: v for k, v in counts.items() if v >= _MIN_OCCURRENCES}
        if not duplicates:
            return []

        worst_count = max(duplicates.values())

        return [
            RefactorRecommendation(
                file_path=abs_path,
                category=FileCategory.SOURCE_CODE,
                smell=CodeSmell.DUPLICATE_CODE,
                technique=RefactorTechnique.EXTRACT_METHOD,
                priority=Priority.MEDIUM,
                description=(
                    f"Found {len(duplicates)} repeated code block(s) "
                    f"(worst: {worst_count}x occurrences, window={_WINDOW} lines).  "
                    f"Extract to shared helper functions or a utility module."
                ),
                estimated_token_reduction=int(file_info.tokens * 0.10),
                details={
                    "duplicate_block_count": len(duplicates),
                    "max_occurrences": worst_count,
                    "window_size": _WINDOW,
                },
            )
        ]
