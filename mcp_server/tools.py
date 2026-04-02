"""Compatibility facade for public MCP tool functions."""

from __future__ import annotations

from .tools_analysis import (
    analyze_project,
    context_budget,
    detect_refactor_candidates_tool,
    generate_refactor_plan_tool,
)
from .tools_heuristics import detect_code_smells, generate_refactor_suggestions

__all__ = [
    "analyze_project",
    "context_budget",
    "detect_code_smells",
    "detect_refactor_candidates_tool",
    "generate_refactor_plan_tool",
    "generate_refactor_suggestions",
]
