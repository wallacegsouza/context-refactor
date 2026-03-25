"""Integration tests for HeuristicsEngine."""

from __future__ import annotations

from pathlib import Path

from context_refactor.models import (
    CodeSmell,
    ContextBudget,
    FileCategory,
    FileTokenInfo,
    RefactorPlan,
    RefactorRecommendation,
    RefactorTechnique,
)
from context_refactor.refactor_heuristics import HeuristicsEngine
from context_refactor.refactor_rules.base import RefactorRule

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


def _make_budget(total_tokens: int = 1000, context_budget: int = 102_400) -> ContextBudget:
    return ContextBudget(
        llm_context_size=128_000,
        safety_margin=0.80,
        context_budget=context_budget,
        total_tokens=total_tokens,
        total_files=10,
        fits_context=total_tokens <= context_budget,
        overflow_tokens=max(0, total_tokens - context_budget),
        overflow_ratio=max(0.0, (total_tokens - context_budget) / context_budget),
    )


def _write_clean_py(tmp_path: Path, name: str = "clean.py") -> str:
    """Write a minimal valid Python file and return its relative path."""
    (tmp_path / name).write_text("x = 1\n")
    return name


# ══════════════════════════════════════════════════════════════════════════════
# Initialization
# ══════════════════════════════════════════════════════════════════════════════


class TestHeuristicsEngineInit:
    def test_default_rules_count(self) -> None:
        engine = HeuristicsEngine()
        assert len(engine._rules) == 4

    def test_extra_rules_appended(self) -> None:
        class NoopRule(RefactorRule):
            def applies_to(self, fi: FileTokenInfo) -> bool:
                return False
            def evaluate(self, fi: FileTokenInfo, pp: str) -> list[RefactorRecommendation]:
                return []

        engine = HeuristicsEngine(extra_rules=[NoopRule()])
        assert len(engine._rules) == 5

    def test_context_window_size_passed_to_large_file_rule(self) -> None:
        from context_refactor.refactor_rules.large_file_rule import LargeFileRule
        engine = HeuristicsEngine(context_window_size=200_000)
        large_file_rules = [r for r in engine._rules if isinstance(r, LargeFileRule)]
        assert len(large_file_rules) == 1
        # threshold should be 15% of 200 000 = 30 000
        assert large_file_rules[0]._threshold == 30_000


# ══════════════════════════════════════════════════════════════════════════════
# analyze_file
# ══════════════════════════════════════════════════════════════════════════════


class TestAnalyzeFile:
    def test_clean_small_file_has_empty_problems(self, tmp_path: Path) -> None:
        name = _write_clean_py(tmp_path)
        fi = _make_file_info(name, tokens=50)
        engine = HeuristicsEngine(context_window_size=128_000)
        result = engine.analyze_file(fi, str(tmp_path))
        assert result.problems == []
        assert result.suggested_refactors == []
        assert result.recommendations == []

    def test_binary_file_returns_empty_recommendations(self, tmp_path: Path) -> None:
        fi = _make_file_info(
            "image.png", tokens=100_000, ext=".png", category=FileCategory.BINARY
        )
        engine = HeuristicsEngine()
        result = engine.analyze_file(fi, str(tmp_path))
        assert result.recommendations == []

    def test_language_detected_from_extension(self, tmp_path: Path) -> None:
        name = _write_clean_py(tmp_path, "script.ts")
        fi = _make_file_info(name, tokens=50, ext=".ts")
        engine = HeuristicsEngine()
        result = engine.analyze_file(fi, str(tmp_path))
        assert result.language == "typescript"

    def test_unknown_extension_language_is_unknown(self, tmp_path: Path) -> None:
        (tmp_path / "file.xyz").write_text("content\n")
        fi = _make_file_info("file.xyz", tokens=50, ext=".xyz")
        engine = HeuristicsEngine()
        result = engine.analyze_file(fi, str(tmp_path))
        assert result.language == "unknown"

    def test_heuristic_result_tokens_matches_file_info(self, tmp_path: Path) -> None:
        name = _write_clean_py(tmp_path)
        fi = _make_file_info(name, tokens=999)
        engine = HeuristicsEngine()
        result = engine.analyze_file(fi, str(tmp_path))
        assert result.tokens == 999

    def test_large_file_triggers_recommendation(self, tmp_path: Path) -> None:
        # context window 1 000; threshold = 150 tokens
        (tmp_path / "large.py").write_text("x = 1\n" * 200)
        fi = _make_file_info("large.py", tokens=200, category=FileCategory.SOURCE_CODE)
        engine = HeuristicsEngine(context_window_size=1_000)
        result = engine.analyze_file(fi, str(tmp_path))
        problems = result.problems
        assert "God File" in problems

    def test_deduplication_prevents_double_report(self, tmp_path: Path) -> None:
        """Both pluggable rule and existing analyzer fire → only one recommendation kept."""
        # Write a real Python god-file that triggers both LargeFileRule and
        # code_refactor's GOD_FILE detection
        body = "\n".join(f"x_{i} = {i}" for i in range(700))
        (tmp_path / "godfile.py").write_text(body)
        fi = _make_file_info("godfile.py", tokens=5_000, category=FileCategory.SOURCE_CODE)
        engine = HeuristicsEngine(context_window_size=128_000)
        result = engine.analyze_file(fi, str(tmp_path))

        # Even though two sources may fire, deduplication keeps one per (file, smell, technique)
        god_file_recs = [
            r for r in result.recommendations
            if r.smell == CodeSmell.GOD_FILE and r.technique == RefactorTechnique.EXTRACT_MODULE
        ]
        assert len(god_file_recs) == 1


# ══════════════════════════════════════════════════════════════════════════════
# analyze_project
# ══════════════════════════════════════════════════════════════════════════════


class TestAnalyzeProject:
    def test_skips_binary_files(self, tmp_path: Path) -> None:
        binary_fi = _make_file_info(
            "image.png", tokens=50_000, ext=".png", category=FileCategory.BINARY
        )
        engine = HeuristicsEngine()
        results = engine.analyze_project([binary_fi], str(tmp_path))
        assert results == []

    def test_skips_configuration_files(self, tmp_path: Path) -> None:
        config_fi = _make_file_info(
            "config.json", tokens=5_000, ext=".json", category=FileCategory.CONFIGURATION
        )
        engine = HeuristicsEngine()
        results = engine.analyze_project([config_fi], str(tmp_path))
        assert results == []

    def test_files_without_findings_excluded(self, tmp_path: Path) -> None:
        name = _write_clean_py(tmp_path)
        fi = _make_file_info(name, tokens=10)
        engine = HeuristicsEngine(context_window_size=128_000)
        results = engine.analyze_project([fi], str(tmp_path))
        assert results == []

    def test_results_sorted_by_tokens_descending(self, tmp_path: Path) -> None:
        # Two large Python files — verify ordering
        (tmp_path / "a.py").write_text("x = 1\n" * 200)
        (tmp_path / "b.py").write_text("x = 1\n" * 200)
        fi_a = _make_file_info("a.py", tokens=5_000)
        fi_b = _make_file_info("b.py", tokens=10_000)
        engine = HeuristicsEngine(context_window_size=1_000)
        results = engine.analyze_project([fi_a, fi_b], str(tmp_path))
        if len(results) >= 2:
            assert results[0].tokens >= results[1].tokens


# ══════════════════════════════════════════════════════════════════════════════
# generate_plan
# ══════════════════════════════════════════════════════════════════════════════


class TestGeneratePlan:
    def test_returns_refactor_plan_instance(self, tmp_path: Path) -> None:
        body = "\n".join(f"x_{i} = {i}" for i in range(700))
        (tmp_path / "godfile.py").write_text(body)
        fi = _make_file_info("godfile.py", tokens=5_000)
        engine = HeuristicsEngine(context_window_size=128_000)
        results = engine.analyze_project([fi], str(tmp_path))
        budget = _make_budget(total_tokens=5_000)
        plan = engine.generate_plan(results, budget)
        assert isinstance(plan, RefactorPlan)

    def test_empty_results_returns_empty_plan(self) -> None:
        engine = HeuristicsEngine()
        budget = _make_budget(total_tokens=500)
        plan = engine.generate_plan([], budget)
        assert plan.steps == []
        assert plan.total_estimated_token_reduction == 0

    def test_plan_aggregates_recommendations_from_all_files(self, tmp_path: Path) -> None:
        body = "\n".join(f"x_{i} = {i}" for i in range(700))
        for name in ["a.py", "b.py"]:
            (tmp_path / name).write_text(body)
        fi_a = _make_file_info("a.py", tokens=5_000)
        fi_b = _make_file_info("b.py", tokens=5_000)
        engine = HeuristicsEngine(context_window_size=128_000)
        results = engine.analyze_project([fi_a, fi_b], str(tmp_path))
        budget = _make_budget(total_tokens=10_000)
        plan = engine.generate_plan(results, budget)
        # Plan should have at least one step since both files have issues
        assert len(plan.steps) >= 1
