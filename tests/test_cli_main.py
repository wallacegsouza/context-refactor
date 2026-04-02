"""Tests for the modularized CLI entrypoint."""

from __future__ import annotations

from typer.testing import CliRunner

from cli.main import app
from mcp_server import tools as mcp_tools

runner = CliRunner()


def test_help_lists_registered_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command_name in ["analyze", "budget", "candidates", "smells", "suggest", "plan", "serve"]:
        assert command_name in result.output


def test_budget_command_routes_shared_options_to_tool(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_context_budget(**kwargs):
        captured.update(kwargs)
        return {
            "llm_context_size": 128_000,
            "safety_margin": 0.8,
            "context_budget": 100,
            "total_tokens": 10,
            "total_files": 1,
            "fits_context": True,
            "overflow_tokens": 0,
            "overflow_ratio": 0.0,
        }

    monkeypatch.setattr(mcp_tools, "context_budget", fake_context_budget)

    result = runner.invoke(
        app,
        [
            "budget",
            str(tmp_path),
            "--json",
            "--profile",
            "source-only",
            "--exclude-dirs",
            "reports,coverage",
            "--dependency-mode",
            "report_only",
            "--dependency-depth-weights",
            "1.0,0.5",
        ],
    )

    assert result.exit_code == 0
    assert '"fits_context": true' in result.output.lower()
    assert captured["project_path"] == str(tmp_path.resolve())
    assert captured["analysis_profile"] == "source-only"
    assert captured["exclude_dirs"] == ["reports", "coverage"]
    assert captured["dependency_mode"] == "report_only"
    assert captured["dependency_depth_weights"] == [1.0, 0.5]


def test_suggest_command_routes_shared_options_to_tool(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_generate_refactor_suggestions(**kwargs):
        captured.update(kwargs)
        return {
            "context_budget": {
                "total_tokens": 10,
                "context_budget": 100,
                "fits_context": True,
            },
            "refactor_plan": {
                "steps": [],
            },
        }

    monkeypatch.setattr(
        mcp_tools,
        "generate_refactor_suggestions",
        fake_generate_refactor_suggestions,
    )

    result = runner.invoke(
        app,
        [
            "suggest",
            str(tmp_path),
            "--json",
            "--exclude-files",
            "*.snap,lint.result.txt",
            "--include-categories",
            "source_code,markdown",
            "--dependency-mode",
            "blended",
            "--dependency-max-depth",
            "4",
        ],
    )

    assert result.exit_code == 0
    assert '"steps": []' in result.output
    assert captured["project_path"] == str(tmp_path.resolve())
    assert captured["exclude_files"] == ["*.snap", "lint.result.txt"]
    assert captured["include_categories"] == ["source_code", "markdown"]
    assert captured["dependency_mode"] == "blended"
    assert captured["dependency_max_depth"] == 4
