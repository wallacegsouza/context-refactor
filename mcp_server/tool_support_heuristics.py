"""Heuristics-domain support helpers for MCP tool wrappers."""

from __future__ import annotations

from typing import Any

from context_refactor.refactor_heuristics import HeuristicsEngine


def create_heuristics_engine(
    llm_context_size: int,
    totals: dict[str, Any],
) -> HeuristicsEngine:
    dependency_mode_resolved = totals.get("dependency_analysis", {}).get("mode")
    return HeuristicsEngine(
        context_window_size=llm_context_size,
        rank_by_dependency=dependency_mode_resolved in {"blended", "weighted"},
    )


__all__ = ["create_heuristics_engine"]
