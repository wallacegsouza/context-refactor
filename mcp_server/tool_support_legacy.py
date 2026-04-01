"""Legacy recommendation support helpers for MCP tool wrappers."""

from __future__ import annotations

from typing import Any

from context_refactor.refactor_engine import detect_refactor_candidates


def dependency_rules_enabled(totals: dict[str, Any]) -> bool:
    mode = totals.get("dependency_analysis", {}).get("mode")
    return mode in {"blended", "weighted"}


def legacy_recommendations(
    file_infos: list[Any],
    project_path: str,
    totals: dict[str, Any],
) -> list[Any]:
    return detect_refactor_candidates(
        file_infos,
        project_path,
        enable_dependency_rules=dependency_rules_enabled(totals),
    )


__all__ = [
    "dependency_rules_enabled",
    "legacy_recommendations",
]
