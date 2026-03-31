"""Tests for the legacy refactor engine with dependency-aware enrichments."""

from __future__ import annotations

from pathlib import Path

from context_refactor.models import (
    CodeSmell,
    FileCategory,
    FileTokenInfo,
    RefactorTechnique,
)
from context_refactor.refactor_engine import detect_refactor_candidates


def _make_coupled_file_info() -> FileTokenInfo:
    return FileTokenInfo(
        path="coupled.py",
        ext=".py",
        tokens=200,
        bytes_=800,
        chars=800,
        category=FileCategory.SOURCE_CODE,
        direct_dependencies_count=8,
        direct_internal_dependencies_count=6,
        direct_external_dependencies_count=2,
        transitive_dependencies_count=15,
        dependency_depth_analyzed=3,
        dependency_weight=2.0,
        effective_token_size=400,
        refactor_priority_score=0.9,
        fan_in=3,
        fan_out=7,
    )


def test_detect_refactor_candidates_keeps_legacy_behavior_by_default(
    tmp_path: Path,
) -> None:
    body = "\n".join(f"x_{i} = {i}" for i in range(30))
    (tmp_path / "coupled.py").write_text(body, encoding="utf-8")

    recs = detect_refactor_candidates([_make_coupled_file_info()], str(tmp_path))

    assert not any(rec.smell == CodeSmell.HIGH_COUPLING for rec in recs)


def test_detect_refactor_candidates_includes_high_coupling_when_enabled(
    tmp_path: Path,
) -> None:
    body = "\n".join(f"x_{i} = {i}" for i in range(30))
    (tmp_path / "coupled.py").write_text(body, encoding="utf-8")

    recs = detect_refactor_candidates(
        [_make_coupled_file_info()],
        str(tmp_path),
        enable_dependency_rules=True,
    )

    assert any(
        rec.smell == CodeSmell.HIGH_COUPLING
        and rec.technique == RefactorTechnique.INVERT_DEPENDENCY
        for rec in recs
    )
