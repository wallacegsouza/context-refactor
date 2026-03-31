"""Tests for MCP tool mode-gating around dependency-aware legacy outputs."""

from __future__ import annotations

from pathlib import Path

from mcp_server.tools import detect_refactor_candidates_tool


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
