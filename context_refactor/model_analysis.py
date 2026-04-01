"""Code and markdown structural model types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FunctionInfo:
    """Basic information about a detected function / method."""

    name: str
    start_line: int
    end_line: int
    line_count: int
    parameter_count: int
    nesting_depth: int = 0


@dataclass(frozen=True)
class ClassInfo:
    """Basic information about a detected class."""

    name: str
    start_line: int
    end_line: int
    line_count: int
    method_count: int


@dataclass(frozen=True)
class MarkdownSection:
    """A heading-delimited section inside a Markdown document."""

    heading: str
    level: int
    start_line: int
    end_line: int
    line_count: int
    suggested_filename: str
