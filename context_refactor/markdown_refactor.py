"""Markdown-specific refactoring: topic-based document splitting.

Analyses Markdown files by their heading structure and proposes splitting
large documents into per-topic files with an index document linking them.
"""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Sequence

from .models import (
    CodeSmell,
    FileCategory,
    MarkdownSection,
    Priority,
    RefactorRecommendation,
    RefactorTechnique,
)

# ── Constants ─────────────────────────────────────────────────────────────────

# Minimum token count to even consider a Markdown file for splitting.
_MIN_TOKENS_FOR_SPLIT = 800

# Minimum number of top-level sections required to justify a split.
_MIN_SECTIONS_FOR_SPLIT = 3

# Split level: only H1 (``#``) and H2 (``##``) create new files.
_SPLIT_MAX_LEVEL = 2

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _slugify(text: str) -> str:
    """Convert a heading text to a safe filename slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text or "section"


# ── Section detection ────────────────────────────────────────────────────────


def detect_sections(filepath: str) -> list[MarkdownSection]:
    """Parse a Markdown file and return its heading-delimited sections."""
    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()

    total_lines = len(lines)
    headings: list[tuple[int, int, str]] = []  # (level, 0-based line, text)

    for idx, line in enumerate(lines):
        m = _HEADING_RE.match(line.rstrip())
        if m:
            level = len(m.group(1))
            headings.append((level, idx, m.group(2).strip()))

    if not headings:
        return []

    sections: list[MarkdownSection] = []
    base_dir = os.path.dirname(filepath)

    for i, (level, start, text) in enumerate(headings):
        if level > _SPLIT_MAX_LEVEL:
            continue
        # Section ends at the next same-or-higher-level heading or EOF
        end = total_lines - 1
        for j in range(i + 1, len(headings)):
            if headings[j][0] <= level:
                end = headings[j][1] - 1
                break

        line_count = end - start + 1
        slug = _slugify(text)
        suggested = f"{slug}.md"

        sections.append(
            MarkdownSection(
                heading=text,
                level=level,
                start_line=start + 1,  # 1-based
                end_line=end + 1,
                line_count=line_count,
                suggested_filename=suggested,
            )
        )

    return sections


# ── Recommendation builder ───────────────────────────────────────────────────


def analyze_markdown(
    filepath: str,
    tokens: int,
    min_tokens: int = _MIN_TOKENS_FOR_SPLIT,
    min_sections: int = _MIN_SECTIONS_FOR_SPLIT,
) -> list[RefactorRecommendation]:
    """Return refactoring recommendations for a single Markdown file.

    Only proposes splitting when the file exceeds *min_tokens* **and**
    contains at least *min_sections* top-level sections.
    """
    if tokens < min_tokens:
        return []

    try:
        sections = detect_sections(filepath)
    except (OSError, UnicodeDecodeError):
        return []

    if len(sections) < min_sections:
        return []

    # Build human-readable description
    section_names = [s.heading for s in sections]
    detail_list = ", ".join(section_names[:8])
    if len(section_names) > 8:
        detail_list += f" … (+{len(section_names) - 8} more)"

    # Estimate: splitting saves ~15 % overhead by allowing selective loading
    estimated_reduction = int(tokens * 0.15)

    return [
        RefactorRecommendation(
            file_path=filepath,
            category=FileCategory.MARKDOWN,
            smell=CodeSmell.GOD_FILE,
            technique=RefactorTechnique.SPLIT_DOCUMENT,
            priority=Priority.MEDIUM if tokens < 2000 else Priority.HIGH,
            description=(
                f"Split into {len(sections)} topic files "
                f"({detail_list}). "
                f"The original becomes an index document."
            ),
            estimated_token_reduction=estimated_reduction,
            details={
                "sections": [
                    {
                        "heading": s.heading,
                        "level": s.level,
                        "lines": s.line_count,
                        "suggested_file": s.suggested_filename,
                    }
                    for s in sections
                ],
            },
        )
    ]
