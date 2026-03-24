"""Unit tests for the pluggable refactoring rule classes."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from context_refactor.models import (
    CodeSmell,
    FileCategory,
    FileTokenInfo,
    Priority,
    RefactorTechnique,
)
from context_refactor.refactor_rules import (
    DuplicateCodeRule,
    LargeClassRule,
    LargeFileRule,
    LongMethodRule,
    RefactorRule,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_file_info(
    path: str,
    tokens: int,
    ext: str = ".py",
    category: FileCategory = FileCategory.SOURCE_CODE,
) -> FileTokenInfo:
    return FileTokenInfo(
        path=path,
        ext=ext,
        tokens=tokens,
        bytes_=tokens * 4,
        chars=tokens * 4,
        category=category,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Abstract base — must not be instantiable
# ══════════════════════════════════════════════════════════════════════════════


def test_refactor_rule_is_abstract() -> None:
    with pytest.raises(TypeError):
        RefactorRule()  # type: ignore[abstract]


# ══════════════════════════════════════════════════════════════════════════════
# LargeFileRule
# ══════════════════════════════════════════════════════════════════════════════


class TestLargeFileRule:
    def test_below_threshold_returns_empty(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000, threshold_pct=0.15)
        # threshold = 19 200
        fi = _make_file_info("file.py", tokens=19_199)
        assert rule.applies_to(fi)
        assert rule.evaluate(fi, str(tmp_path)) == []

    def test_at_threshold_returns_empty(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000, threshold_pct=0.15)
        fi = _make_file_info("file.py", tokens=19_200)
        # 19 200 < threshold? threshold = int(128000 * 0.15) = 19 200, not <
        # Actually tokens < threshold is the condition, so exactly at threshold triggers
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) == 1

    def test_above_threshold_emits_recommendation(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000, threshold_pct=0.15)
        fi = _make_file_info("file.py", tokens=20_000)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) == 1
        rec = recs[0]
        assert rec.smell == CodeSmell.GOD_FILE
        assert rec.technique == RefactorTechnique.EXTRACT_MODULE
        assert rec.priority == Priority.HIGH

    def test_double_threshold_gives_critical(self, tmp_path: Path) -> None:
        # threshold = 19 200; 2× = 38 400
        rule = LargeFileRule(context_window_size=128_000, threshold_pct=0.15)
        fi = _make_file_info("file.py", tokens=38_400)
        recs = rule.evaluate(fi, str(tmp_path))
        assert recs[0].priority == Priority.CRITICAL

    def test_estimated_reduction_is_30_percent(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000, threshold_pct=0.15)
        fi = _make_file_info("file.py", tokens=40_000)
        rec = rule.evaluate(fi, str(tmp_path))[0]
        assert rec.estimated_token_reduction == int(40_000 * 0.30)

    def test_details_contain_expected_keys(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000, threshold_pct=0.15)
        fi = _make_file_info("file.py", tokens=25_000)
        rec = rule.evaluate(fi, str(tmp_path))[0]
        assert "tokens" in rec.details
        assert "threshold" in rec.details
        assert "pct_of_window" in rec.details

    def test_binary_file_not_applicable(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000)
        fi = _make_file_info("image.png", tokens=50_000, ext=".png", category=FileCategory.BINARY)
        assert not rule.applies_to(fi)

    def test_markdown_file_is_applicable(self, tmp_path: Path) -> None:
        rule = LargeFileRule(context_window_size=128_000)
        fi = _make_file_info("readme.md", tokens=25_000, ext=".md", category=FileCategory.MARKDOWN)
        assert rule.applies_to(fi)


# ══════════════════════════════════════════════════════════════════════════════
# LongMethodRule
# ══════════════════════════════════════════════════════════════════════════════


def _write_py_with_function(path: Path, func_lines: int) -> FileTokenInfo:
    """Write a Python file containing a function of *func_lines* body lines."""
    body = "\n".join(f"    x_{i} = {i}" for i in range(func_lines))
    source = f"def long_function():\n{body}\n"
    (path / "target.py").write_text(source)
    return _make_file_info("target.py", tokens=func_lines * 2)


class TestLongMethodRule:
    def test_long_function_triggers(self, tmp_path: Path) -> None:
        rule = LongMethodRule(threshold_lines=80)
        fi = _write_py_with_function(tmp_path, func_lines=80)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) >= 1
        assert recs[0].smell == CodeSmell.LONG_METHOD
        assert recs[0].technique == RefactorTechnique.EXTRACT_METHOD

    def test_short_function_does_not_trigger(self, tmp_path: Path) -> None:
        rule = LongMethodRule(threshold_lines=80)
        fi = _write_py_with_function(tmp_path, func_lines=10)
        recs = rule.evaluate(fi, str(tmp_path))
        assert recs == []

    def test_details_contain_function_name(self, tmp_path: Path) -> None:
        rule = LongMethodRule(threshold_lines=5)
        fi = _write_py_with_function(tmp_path, func_lines=10)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) >= 1
        assert "function" in recs[0].details

    def test_markdown_not_applicable(self) -> None:
        rule = LongMethodRule()
        fi = _make_file_info("doc.md", tokens=100, ext=".md", category=FileCategory.MARKDOWN)
        assert not rule.applies_to(fi)

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        rule = LongMethodRule(threshold_lines=5)
        fi = _make_file_info("nonexistent.py", tokens=200)
        assert rule.evaluate(fi, str(tmp_path)) == []


# ══════════════════════════════════════════════════════════════════════════════
# LargeClassRule
# ══════════════════════════════════════════════════════════════════════════════


def _write_py_class(path: Path, body_lines: int, num_methods: int = 0) -> FileTokenInfo:
    """Write a Python file containing a class of *body_lines* total lines."""
    methods = "\n".join(
        f"    def method_{i}(self):\n        pass" for i in range(num_methods)
    )
    filler = "\n".join(f"    attr_{i} = {i}" for i in range(max(0, body_lines - num_methods * 3)))
    source = f"class BigClass:\n{methods}\n{filler}\n"
    (path / "target.py").write_text(source)
    return _make_file_info("target.py", tokens=body_lines * 3)


class TestLargeClassRule:
    def test_large_class_by_lines(self, tmp_path: Path) -> None:
        rule = LargeClassRule(threshold_lines=50, threshold_methods=100)
        fi = _write_py_class(tmp_path, body_lines=55)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) >= 1
        assert recs[0].smell == CodeSmell.LARGE_CLASS

    def test_small_class_does_not_trigger(self, tmp_path: Path) -> None:
        rule = LargeClassRule(threshold_lines=500, threshold_methods=20)
        fi = _write_py_class(tmp_path, body_lines=10)
        recs = rule.evaluate(fi, str(tmp_path))
        assert recs == []

    def test_large_class_by_method_count(self, tmp_path: Path) -> None:
        rule = LargeClassRule(threshold_lines=10_000, threshold_methods=5)
        fi = _write_py_class(tmp_path, body_lines=30, num_methods=6)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) >= 1
        assert recs[0].smell == CodeSmell.LARGE_CLASS

    def test_details_contain_class_name(self, tmp_path: Path) -> None:
        rule = LargeClassRule(threshold_lines=5, threshold_methods=100)
        fi = _write_py_class(tmp_path, body_lines=10)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) >= 1
        assert "class" in recs[0].details

    def test_markdown_not_applicable(self) -> None:
        rule = LargeClassRule()
        fi = _make_file_info("doc.md", tokens=100, ext=".md", category=FileCategory.MARKDOWN)
        assert not rule.applies_to(fi)


# ══════════════════════════════════════════════════════════════════════════════
# DuplicateCodeRule
# ══════════════════════════════════════════════════════════════════════════════


def _write_duplicate_file(path: Path, repetitions: int, window: int = 5) -> FileTokenInfo:
    """Write a file containing a *window*-line block repeated *repetitions* times."""
    block = "\n".join(f"line_{i} = {i}" for i in range(window))
    content = "\n".join([block] * repetitions + ["# end\n"])
    (path / "dup.py").write_text(content)
    total_lines = window * repetitions + 1
    return _make_file_info("dup.py", tokens=total_lines * 3)


class TestDuplicateCodeRule:
    def test_repeated_block_triggers(self, tmp_path: Path) -> None:
        rule = DuplicateCodeRule()
        fi = _write_duplicate_file(tmp_path, repetitions=3)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) == 1
        assert recs[0].smell == CodeSmell.DUPLICATE_CODE

    def test_two_repetitions_does_not_trigger(self, tmp_path: Path) -> None:
        rule = DuplicateCodeRule()
        fi = _write_duplicate_file(tmp_path, repetitions=2)
        recs = rule.evaluate(fi, str(tmp_path))
        assert recs == []

    def test_fast_exit_for_short_file(self, tmp_path: Path) -> None:
        rule = DuplicateCodeRule()
        (tmp_path / "short.py").write_text("x = 1\ny = 2\n")
        fi = _make_file_info("short.py", tokens=10)
        assert rule.evaluate(fi, str(tmp_path)) == []

    def test_details_contain_block_count_and_max_occurrences(self, tmp_path: Path) -> None:
        rule = DuplicateCodeRule()
        fi = _write_duplicate_file(tmp_path, repetitions=4)
        recs = rule.evaluate(fi, str(tmp_path))
        assert len(recs) == 1
        assert "duplicate_block_count" in recs[0].details
        assert "max_occurrences" in recs[0].details
        assert recs[0].details["max_occurrences"] >= 4

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        rule = DuplicateCodeRule()
        fi = _make_file_info("ghost.py", tokens=500)
        assert rule.evaluate(fi, str(tmp_path)) == []

    def test_configuration_not_applicable(self) -> None:
        rule = DuplicateCodeRule()
        fi = _make_file_info("config.json", tokens=100, ext=".json", category=FileCategory.CONFIGURATION)
        assert not rule.applies_to(fi)
