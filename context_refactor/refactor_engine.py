"""Refactor engine — orchestrator that routes files to the correct analyser.

Consumes the token-analysis output from :mod:`analyzer` and delegates to:

* :mod:`markdown_refactor` for ``.md`` / ``.mdx`` files
* :mod:`code_refactor` for source-code files
* (No-op for configuration and binary files)

Returns a flat list of :class:`RefactorRecommendation` instances sorted by
estimated impact.
"""

from __future__ import annotations

import os
from typing import Sequence

from .models import (
    FileCategory,
    FileTokenInfo,
    RefactorRecommendation,
)
from .markdown_refactor import analyze_markdown
from .code_refactor import analyze_source_file


def detect_refactor_candidates(
    file_infos: Sequence[FileTokenInfo],
    project_path: str,
) -> list[RefactorRecommendation]:
    """Scan every file and collect all refactoring recommendations.

    Parameters
    ----------
    file_infos:
        Token-annotated file list produced by :func:`analyzer.analyze_tokens`.
    project_path:
        Absolute path to the project root (used to resolve relative paths).

    Returns
    -------
    list[RefactorRecommendation]
        Flat list sorted by ``estimated_token_reduction`` descending.
    """
    recommendations: list[RefactorRecommendation] = []

    for info in file_infos:
        abs_path = os.path.join(project_path, info.path)

        if not os.path.isfile(abs_path):
            continue

        if info.category == FileCategory.MARKDOWN:
            recs = analyze_markdown(abs_path, tokens=info.tokens)
            recommendations.extend(recs)

        elif info.category == FileCategory.SOURCE_CODE:
            recs = analyze_source_file(abs_path, tokens=info.tokens)
            recommendations.extend(recs)

        # Configuration and binary files are intentionally skipped.

    # Sort by estimated token reduction (biggest wins first)
    recommendations.sort(
        key=lambda r: r.estimated_token_reduction, reverse=True
    )
    return recommendations
