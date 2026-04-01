"""Tests for MCP tool mode-gating around dependency-aware legacy outputs."""

from __future__ import annotations

from pathlib import Path

from mcp_server import tool_support
from mcp_server.tools import (
    analyze_project,
    detect_refactor_candidates_tool,
    generate_refactor_suggestions,
)


def _write_coupled_python_package(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for name in ["b", "c", "d", "e", "f", "g"]:
        (pkg / f"{name}.py").write_text(f"VALUE_{name} = {len(name)}\n", encoding="utf-8")

    (pkg / "a.py").write_text(
        "\n".join(
            [
                "from pkg import b, c, d, e, f, g",
                "",
                "def run():",
                "    return (",
                "        b.VALUE_b + c.VALUE_c + d.VALUE_d +",
                "        e.VALUE_e + f.VALUE_f + g.VALUE_g",
                "    )",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_detect_refactor_candidates_tool_keeps_legacy_output_in_report_only(
    tmp_path: Path,
) -> None:
    _write_coupled_python_package(tmp_path)

    result = detect_refactor_candidates_tool(
        project_path=str(tmp_path),
        dependency_mode="report_only",
        dependency_max_depth=3,
    )

    smells = {rec["smell"] for rec in result["recommendations"]}
    assert result["compatibility_mode"] == "report_only"
    assert "High Coupling" not in smells


def test_detect_refactor_candidates_tool_enables_high_coupling_in_blended_mode(
    tmp_path: Path,
) -> None:
    _write_coupled_python_package(tmp_path)

    result = detect_refactor_candidates_tool(
        project_path=str(tmp_path),
        dependency_mode="blended",
        dependency_max_depth=3,
    )

    smells = {rec["smell"] for rec in result["recommendations"]}
    assert result["compatibility_mode"] == "blended"
    assert "High Coupling" in smells


def test_analyze_project_returns_shared_metadata_and_plan(tmp_path: Path) -> None:
    _write_coupled_python_package(tmp_path)

    result = analyze_project(
        project_path=str(tmp_path),
        dependency_mode="blended",
        dependency_max_depth=3,
        top_n=10,
    )

    assert result["compatibility_mode"] == "blended"
    assert "analysis_scope" in result
    assert "noise_summary" in result
    assert "dependency_analysis" in result
    assert "dependency_hotspots" in result
    assert "project_summary" in result
    assert "context_budget" in result
    assert "refactor_plan" in result


def test_generate_refactor_suggestions_returns_heuristics_and_plan(tmp_path: Path) -> None:
    _write_coupled_python_package(tmp_path)

    result = generate_refactor_suggestions(
        project_path=str(tmp_path),
        dependency_mode="blended",
        dependency_max_depth=3,
    )

    assert result["compatibility_mode"] == "blended"
    assert "heuristic_results" in result
    assert "refactor_plan" in result
    assert "dependency_hotspots" in result


def test_tool_support_facade_reexports_domain_helpers() -> None:
    assert callable(tool_support.run_token_analysis)
    assert callable(tool_support.compute_budget_from_totals)
    assert callable(tool_support.create_heuristics_engine)
    assert callable(tool_support.legacy_recommendations)
    assert callable(tool_support.shared_response_fields)
