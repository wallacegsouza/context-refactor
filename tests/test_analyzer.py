"""Tests for analysis scope resolution and scanner noise reduction."""

from __future__ import annotations

import json

from context_refactor.analyzer import analyze_tokens


def test_default_profile_excludes_generated_dirs(tmp_path) -> None:
    (tmp_path / "coverage").mkdir()
    (tmp_path / "coverage" / "index.html").write_text("<html>coverage</html>\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("export const answer = 42;\n", encoding="utf-8")

    file_infos, _, totals = analyze_tokens(str(tmp_path), estimator="bytes", top_n=10)

    paths = {info.path for info in file_infos}
    assert "src/app.ts" in paths
    assert "coverage/index.html" not in paths
    assert totals["analysis_scope"]["profile"] == "default"
    assert "coverage" in totals["analysis_scope"]["exclude_dirs"]


def test_full_profile_keeps_generated_dirs(tmp_path) -> None:
    (tmp_path / "coverage").mkdir()
    (tmp_path / "coverage" / "index.html").write_text("<html>coverage</html>\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("export const answer = 42;\n", encoding="utf-8")

    file_infos, _, totals = analyze_tokens(
        str(tmp_path),
        estimator="bytes",
        top_n=10,
        analysis_profile="full",
    )

    paths = {info.path for info in file_infos}
    assert "src/app.ts" in paths
    assert "coverage/index.html" in paths
    assert totals["analysis_scope"]["profile"] == "full"


def test_source_only_profile_filters_non_source_categories(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("export const answer = 42;\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Notes\n", encoding="utf-8")

    file_infos, _, totals = analyze_tokens(
        str(tmp_path),
        estimator="bytes",
        top_n=10,
        analysis_profile="source-only",
    )

    assert [info.path for info in file_infos] == ["src/app.ts"]
    assert totals["files"] == 1
    assert totals["category_counts"] == {"source_code": 1}
    assert totals["noise_summary"]["scanner_files"] == 2
    assert totals["noise_summary"]["files_after_filters"] == 1
    assert totals["noise_summary"]["filtered_by_category_files"] == 1
    assert totals["noise_summary"]["scanner_category_counts"]["source_code"] == 1
    assert totals["noise_summary"]["scanner_category_counts"]["markdown"] == 1
    assert totals["signal_score"]["value"] == 100.0
    assert totals["signal_score"]["noise_ratio"] == 0.0
    assert totals["signal_score"]["total_tokens"] == totals["tokens"]


def test_repo_config_excludes_nested_directory_glob(tmp_path) -> None:
    (tmp_path / "docs" / "planning").mkdir(parents=True)
    (tmp_path / "docs" / "planning" / "plan.md").write_text("# Planning\n", encoding="utf-8")
    (tmp_path / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (tmp_path / ".context-refactor.json").write_text(
        json.dumps({"analysis": {"exclude_globs": ["docs/planning"]}}),
        encoding="utf-8",
    )

    file_infos, _, totals = analyze_tokens(str(tmp_path), estimator="bytes", top_n=10)

    paths = {info.path for info in file_infos}
    assert "docs/guide.md" in paths
    assert "docs/planning/plan.md" not in paths
    assert totals["analysis_scope"]["config_path"].endswith(".context-refactor.json")


def test_explicit_profile_overrides_repo_config_profile(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("export const answer = 42;\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Notes\n", encoding="utf-8")
    (tmp_path / ".context-refactor.json").write_text(
        json.dumps({"analysis": {"analysis_profile": "default"}}),
        encoding="utf-8",
    )

    file_infos, _, totals = analyze_tokens(
        str(tmp_path),
        estimator="bytes",
        top_n=10,
        analysis_profile="source-only",
    )

    assert totals["analysis_scope"]["profile"] == "source-only"
    assert [info.path for info in file_infos] == ["src/app.ts"]


def test_dependency_analysis_enriches_source_files_when_enabled(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text(
        "import json\nimport src.b as b\n\ndef run():\n    return b.answer()\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "b.py").write_text(
        "import src.c as c\n\ndef answer():\n    return c.VALUE\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "c.py").write_text("VALUE = 42\n", encoding="utf-8")

    file_infos, _, totals = analyze_tokens(
        str(tmp_path),
        estimator="bytes",
        top_n=10,
        dependency_mode="report_only",
        dependency_max_depth=3,
    )

    by_path = {info.path: info for info in file_infos}
    a_info = by_path["src/a.py"]

    assert totals["dependency_analysis"]["enabled"] is True
    assert totals["dependency_analysis"]["mode"] == "report_only"
    assert totals["dependency_analysis"]["dependency_metrics_version"] == 1
    assert totals["report_schema_version"] == 2
    assert totals["compatibility_mode"] == "report_only"
    assert totals["dependency_analysis"]["effective_tokens"] >= totals["tokens"]
    assert a_info.direct_dependencies_count >= 2
    assert a_info.direct_internal_dependencies_count >= 1
    assert a_info.direct_external_dependencies_count >= 1
    assert a_info.transitive_dependencies_count >= 1
    assert a_info.effective_token_size >= a_info.tokens
    assert a_info.refactor_priority_score > 0.0


def test_dependency_analysis_resolves_python_from_import_submodule(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "a.py").write_text(
        "from src import b\n\ndef run():\n    return b.answer()\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "b.py").write_text(
        "from src import c\n\ndef answer():\n    return c.VALUE\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "c.py").write_text("VALUE = 42\n", encoding="utf-8")

    file_infos, _, totals = analyze_tokens(
        str(tmp_path),
        estimator="bytes",
        top_n=10,
        dependency_mode="report_only",
        dependency_max_depth=3,
    )

    by_path = {info.path: info for info in file_infos}
    a_info = by_path["src/a.py"]

    assert totals["dependency_analysis"]["enabled"] is True
    assert a_info.direct_internal_dependencies_count >= 1
    assert a_info.transitive_dependencies_count >= 1
