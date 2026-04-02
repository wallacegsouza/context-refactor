from __future__ import annotations

import argparse
import json

from token_report import build_runtime_config, generate_report, write_outputs


def _build_args(tmp_path):
    return argparse.Namespace(
        root=str(tmp_path),
        include_ext="py,md",
        exclude_dirs="build,.git",
        exclude_globs="*.snap",
        exclude_files="README.md",
        extra_exclude_dirs="reports",
        extra_exclude_globs="*.min.js",
        extra_exclude_files="notes.md",
        use_gitignore=False,
        max_mb=5.0,
        follow_symlinks=False,
        depth=2,
        out_csv=str(tmp_path / "token-report" / "files.csv"),
        out_json=str(tmp_path / "token-report" / "files.json"),
        out_md=str(tmp_path / "token-report" / "summary.md"),
        no_json=False,
        no_md=False,
        top=10,
        chart=False,
        chart_kind="bar",
        chart_top=10,
        chart_width=10.0,
        chart_height=6.0,
        chart_dpi=120,
        estimator="bytes",
    )


def test_build_runtime_config_merges_default_and_extra_exclusions(tmp_path) -> None:
    config = build_runtime_config(_build_args(tmp_path))

    assert config.include_ext == {".py", ".md"}
    assert config.exclude_dirs == {"build", ".git", "reports"}
    assert config.exclude_globs == ["*.snap", "*.min.js"]
    assert config.exclude_files == ["README.md", "notes.md"]
    assert config.write_json is True
    assert config.write_md is True


def test_generate_report_and_write_outputs_preserve_filtered_scan(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello world')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# ignored\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# ignored too\n", encoding="utf-8")

    config = build_runtime_config(_build_args(tmp_path))
    rows, dir_rows, totals = generate_report(config)
    write_outputs(config, rows, dir_rows, totals)

    assert [row["path"] for row in rows] == ["src/app.py"]
    assert totals["files"] == 1
    assert dir_rows[0]["dir"] == "src/app.py"

    payload = json.loads((tmp_path / "token-report" / "files.json").read_text(encoding="utf-8"))
    assert payload["totals"]["files"] == 1
    assert payload["files"][0]["path"] == "src/app.py"

    markdown = (tmp_path / "token-report" / "summary.md").read_text(encoding="utf-8")
    assert "Token Count Report (Estimated)" in markdown
    assert "src/app.py" in markdown
