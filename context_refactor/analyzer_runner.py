"""Token report execution helpers."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

PACKAGE_DIR = Path(__file__).resolve().parent
TOKEN_REPORT_SCRIPT = PACKAGE_DIR.parent / "token_report.py"


def run_token_report(
    project_path: str,
    estimator: str = "bytes",
    extra_args: list[str] | None = None,
    extra_exclude_dirs: list[str] | None = None,
    extra_exclude_globs: list[str] | None = None,
    extra_exclude_files: list[str] | None = None,
) -> dict[str, Any]:
    """Execute ``token_report.py`` and return its JSON output."""
    if not TOKEN_REPORT_SCRIPT.is_file():
        raise FileNotFoundError(
            f"token_report.py not found at {TOKEN_REPORT_SCRIPT}. "
            "Ensure it is located alongside the context_refactor package."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        out_json = os.path.join(tmpdir, "report.json")
        cmd: list[str] = [
            "python3",
            str(TOKEN_REPORT_SCRIPT),
            "--root",
            str(project_path),
            "--estimator",
            estimator,
            "--out-json",
            out_json,
            "--out-csv",
            os.path.join(tmpdir, "report.csv"),
            "--out-md",
            os.path.join(tmpdir, "report.md"),
            "--use-gitignore",
        ]
        if extra_exclude_dirs:
            cmd.extend(["--extra-exclude-dirs", ",".join(extra_exclude_dirs)])
        if extra_exclude_globs:
            cmd.extend(["--extra-exclude-globs", ",".join(extra_exclude_globs)])
        if extra_exclude_files:
            cmd.extend(["--extra-exclude-files", ",".join(extra_exclude_files)])
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"token_report.py failed (exit {result.returncode}):\n{result.stderr}"
            )

        with open(out_json, encoding="utf-8") as handle:
            return cast(dict[str, Any], json.load(handle))
