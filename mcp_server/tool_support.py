"""Compatibility facade for MCP tool support helpers."""

from __future__ import annotations

from .tool_support_analysis import (
    analysis_kwargs,
    compute_budget_from_totals,
    dependency_kwargs,
    project_summary,
    run_token_analysis,
    shared_response_fields,
)
from .tool_support_heuristics import create_heuristics_engine
from .tool_support_legacy import dependency_rules_enabled, legacy_recommendations

__all__ = [
    "analysis_kwargs",
    "compute_budget_from_totals",
    "create_heuristics_engine",
    "dependency_kwargs",
    "dependency_rules_enabled",
    "legacy_recommendations",
    "project_summary",
    "run_token_analysis",
    "shared_response_fields",
]
