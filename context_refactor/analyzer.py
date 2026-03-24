"""Analyzer — thin wrapper around ``token_report.py``.

This module is the **only** place that invokes the external token-reporting
script.  Everything else in the package consumes the parsed output via the
domain models defined in ``models.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from .models import (
    DirectoryTokenInfo,
    FileCategory,
    FileTokenInfo,
)

# ── File classification ──────────────────────────────────────────────────────

_SOURCE_EXTS: set[str] = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".go",
    ".rb", ".php", ".rs", ".c", ".h", ".cpp", ".hpp", ".cs",
    ".swift", ".scala", ".lua", ".sh", ".bash", ".zsh",
}

_CONFIG_EXTS: set[str] = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env",
    ".xml", ".properties", ".conf",
}

_CONFIG_NAMES: set[str] = {
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "makefile", ".editorconfig", ".prettierrc", ".eslintrc",
    "tsconfig.json", "package.json", "pyproject.toml", "setup.cfg",
    "cargo.toml", "go.mod", "go.sum", "gemfile", "requirements.txt",
    "pipfile", "pom.xml", "build.gradle", "settings.gradle",
    ".gitignore", ".dockerignore", "vercel.json", "nest-cli.json",
    "vite.config.ts", "tailwind.config.ts", "postcss.config.js",
    "stryker.conf.cjs", "eslint.config.mjs", "eslint.config.js",
    "components.json",
}

_MARKDOWN_EXTS: set[str] = {".md", ".mdx", ".rst"}

_BINARY_EXTS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".o", ".a",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv",
    ".wasm", ".pyc", ".class",
}

_DEFAULT_CONFIG_FILENAME = ".context-refactor.json"
_NOISE_REDUCTION_DIRS: list[str] = [
    "coverage",
    "lcov-report",
    "reports",
    "token-report",
]
_NOISE_REDUCTION_GLOBS: list[str] = [
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.snap",
]
_NOISE_REDUCTION_FILES: list[str] = [
    "lint.result.txt",
]
_PROFILE_DEFAULTS: dict[str, dict[str, list[str]]] = {
    "default": {
        "exclude_dirs": _NOISE_REDUCTION_DIRS,
        "exclude_globs": _NOISE_REDUCTION_GLOBS,
        "exclude_files": _NOISE_REDUCTION_FILES,
        "include_categories": [],
        "exclude_categories": [],
    },
    "full": {
        "exclude_dirs": [],
        "exclude_globs": [],
        "exclude_files": [],
        "include_categories": [],
        "exclude_categories": [],
    },
    "source-only": {
        "exclude_dirs": _NOISE_REDUCTION_DIRS,
        "exclude_globs": _NOISE_REDUCTION_GLOBS,
        "exclude_files": _NOISE_REDUCTION_FILES,
        "include_categories": [FileCategory.SOURCE_CODE.value],
        "exclude_categories": [],
    },
    "docs": {
        "exclude_dirs": _NOISE_REDUCTION_DIRS,
        "exclude_globs": _NOISE_REDUCTION_GLOBS,
        "exclude_files": _NOISE_REDUCTION_FILES,
        "include_categories": [FileCategory.MARKDOWN.value],
        "exclude_categories": [],
    },
}
_VALID_CATEGORY_VALUES = {category.value for category in FileCategory}


def classify_file(path: str, ext: str) -> FileCategory:
    """Return a :class:`FileCategory` for the given file path / extension."""
    ext_lower = ext.lower()
    name_lower = os.path.basename(path).lower()

    if ext_lower in _BINARY_EXTS:
        return FileCategory.BINARY
    if ext_lower in _MARKDOWN_EXTS:
        return FileCategory.MARKDOWN
    if ext_lower in _CONFIG_EXTS or name_lower in _CONFIG_NAMES:
        return FileCategory.CONFIGURATION
    if ext_lower in _SOURCE_EXTS:
        return FileCategory.SOURCE_CODE
    # Fallback: treat recognised text extensions as source
    if ext_lower in {".html", ".css", ".scss", ".sql", ".csv", ".txt"}:
        return FileCategory.OTHER
    return FileCategory.OTHER


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return _split_csv(value)
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized
    raise ValueError(f"Expected string or list for analysis option, got {type(value).__name__}")


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


def _normalize_categories(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        candidate = value.strip().lower()
        if not candidate:
            continue
        if candidate not in _VALID_CATEGORY_VALUES:
            raise ValueError(
                "Unknown category "
                f"'{value}'. Valid values: {', '.join(sorted(_VALID_CATEGORY_VALUES))}"
            )
        normalized.append(candidate)
    return _merge_unique(normalized)


def _load_analysis_config(
    project_path: str,
    config_path: str | None = None,
) -> tuple[dict[str, Any], str | None]:
    candidate = Path(config_path).resolve() if config_path else Path(project_path) / _DEFAULT_CONFIG_FILENAME
    if not candidate.is_file():
        return {}, None

    with candidate.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("ContextRefactor config must be a JSON object")

    if isinstance(data.get("analysis"), dict):
        data = data["analysis"]

    return data, str(candidate)


def _resolve_analysis_scope(
    project_path: str,
    analysis_profile: str,
    config_path: str | None,
    exclude_dirs: list[str] | None,
    exclude_globs: list[str] | None,
    exclude_files: list[str] | None,
    include_categories: list[str] | None,
    exclude_categories: list[str] | None,
) -> dict[str, Any]:
    config, resolved_config_path = _load_analysis_config(project_path, config_path=config_path)
    requested_profile = (analysis_profile or "default").strip().lower()
    if requested_profile and requested_profile != "default":
        profile = requested_profile
    else:
        profile = str(config.get("analysis_profile", requested_profile)).strip().lower()
    if profile not in _PROFILE_DEFAULTS:
        raise ValueError(
            f"Unknown analysis profile '{profile}'. Valid profiles: {', '.join(sorted(_PROFILE_DEFAULTS))}"
        )

    profile_defaults = _PROFILE_DEFAULTS[profile]
    config_exclude_dirs = _normalize_list(config.get("exclude_dirs"))
    config_exclude_globs = _normalize_list(config.get("exclude_globs"))
    config_exclude_files = _normalize_list(config.get("exclude_files"))
    config_include_categories = _normalize_categories(_normalize_list(config.get("include_categories")))
    config_exclude_categories = _normalize_categories(_normalize_list(config.get("exclude_categories")))

    resolved_include_categories = _normalize_categories(
        _merge_unique(
            profile_defaults.get("include_categories", []),
            config_include_categories,
            _normalize_list(include_categories),
        )
    )
    resolved_exclude_categories = _normalize_categories(
        _merge_unique(
            profile_defaults.get("exclude_categories", []),
            config_exclude_categories,
            _normalize_list(exclude_categories),
        )
    )

    return {
        "profile": profile,
        "config_path": resolved_config_path,
        "exclude_dirs": _merge_unique(
            profile_defaults.get("exclude_dirs", []),
            config_exclude_dirs,
            _normalize_list(exclude_dirs),
        ),
        "exclude_globs": _merge_unique(
            profile_defaults.get("exclude_globs", []),
            config_exclude_globs,
            _normalize_list(exclude_globs),
        ),
        "exclude_files": _merge_unique(
            profile_defaults.get("exclude_files", []),
            config_exclude_files,
            _normalize_list(exclude_files),
        ),
        "include_categories": resolved_include_categories,
        "exclude_categories": resolved_exclude_categories,
    }


def _aggregate_directories(
    file_infos: list[FileTokenInfo],
    depth: int = 2,
) -> list[DirectoryTokenInfo]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "tokens": 0, "bytes": 0})
    for info in file_infos:
        parts = [part for part in info.path.split("/") if part]
        directory = "/".join(parts[:depth]) if parts else "."
        grouped[directory]["files"] += 1
        grouped[directory]["tokens"] += info.tokens
        grouped[directory]["bytes"] += info.bytes_

    dir_infos = [
        DirectoryTokenInfo(
            directory=directory,
            files=data["files"],
            tokens=data["tokens"],
            bytes_=data["bytes"],
        )
        for directory, data in grouped.items()
    ]
    dir_infos.sort(key=lambda item: item.tokens, reverse=True)
    return dir_infos


# ── Token report runner ──────────────────────────────────────────────────────

# Resolve path to the bundled ``token_report.py`` (lives next to this package).
_PACKAGE_DIR = Path(__file__).resolve().parent
_TOKEN_REPORT_SCRIPT = _PACKAGE_DIR.parent / "token_report.py"


def _run_token_report(
    project_path: str,
    estimator: str = "bytes",
    extra_args: list[str] | None = None,
    extra_exclude_dirs: list[str] | None = None,
    extra_exclude_globs: list[str] | None = None,
    extra_exclude_files: list[str] | None = None,
) -> dict[str, Any]:
    """Execute ``token_report.py`` and return its JSON output.

    Parameters
    ----------
    project_path:
        Absolute (or relative) path to the project root.
    estimator:
        One of ``bytes``, ``chars``, ``whitespace``, ``heuristic``.
    extra_args:
        Additional CLI flags forwarded to the script.

    Returns
    -------
    dict
        Parsed JSON with keys ``totals``, ``files``, ``dirs``.
    """
    if not _TOKEN_REPORT_SCRIPT.is_file():
        raise FileNotFoundError(
            f"token_report.py not found at {_TOKEN_REPORT_SCRIPT}. "
            "Ensure it is located alongside the context_refactor package."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        out_json = os.path.join(tmpdir, "report.json")
        cmd: list[str] = [
            "python3",
            str(_TOKEN_REPORT_SCRIPT),
            "--root", str(project_path),
            "--estimator", estimator,
            "--out-json", out_json,
            "--out-csv", os.path.join(tmpdir, "report.csv"),
            "--out-md", os.path.join(tmpdir, "report.md"),
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

        with open(out_json, encoding="utf-8") as fh:
            return json.load(fh)


# ── Public API ───────────────────────────────────────────────────────────────


def analyze_tokens(
    project_path: str,
    estimator: str = "bytes",
    top_n: int = 50,
    analysis_profile: str = "default",
    config_path: str | None = None,
    exclude_dirs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    exclude_files: list[str] | None = None,
    include_categories: list[str] | None = None,
    exclude_categories: list[str] | None = None,
) -> tuple[list[FileTokenInfo], list[DirectoryTokenInfo], dict[str, Any]]:
    """Run token analysis and return classified results.

    Returns
    -------
    tuple
        (file_infos, dir_infos, raw_totals)
    """
    analysis_scope = _resolve_analysis_scope(
        project_path=project_path,
        analysis_profile=analysis_profile,
        config_path=config_path,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        exclude_files=exclude_files,
        include_categories=include_categories,
        exclude_categories=exclude_categories,
    )
    raw = _run_token_report(
        project_path,
        estimator=estimator,
        extra_exclude_dirs=analysis_scope["exclude_dirs"],
        extra_exclude_globs=analysis_scope["exclude_globs"],
        extra_exclude_files=analysis_scope["exclude_files"],
    )
    totals: dict[str, Any] = dict(raw.get("totals", {}))

    file_infos: list[FileTokenInfo] = []
    for entry in raw.get("files", []):
        path = entry.get("path", "")
        ext = entry.get("ext", "")
        category = classify_file(path, ext)
        file_infos.append(
            FileTokenInfo(
                path=path,
                ext=ext,
                tokens=entry.get("tokens", 0),
                bytes_=entry.get("bytes", 0),
                chars=entry.get("chars", 0),
                category=category,
            )
        )

    scanner_files = len(file_infos)
    scanner_tokens = sum(file_info.tokens for file_info in file_infos)

    scanner_category_counts: dict[str, int] = defaultdict(int)
    scanner_category_tokens: dict[str, int] = defaultdict(int)
    for file_info in file_infos:
        scanner_category_counts[file_info.category.value] += 1
        scanner_category_tokens[file_info.category.value] += file_info.tokens

    include_category_set = set(analysis_scope["include_categories"])
    exclude_category_set = set(analysis_scope["exclude_categories"])
    if include_category_set:
        file_infos = [fi for fi in file_infos if fi.category.value in include_category_set]
    if exclude_category_set:
        file_infos = [fi for fi in file_infos if fi.category.value not in exclude_category_set]

    dir_infos = _aggregate_directories(file_infos)

    category_counts: dict[str, int] = defaultdict(int)
    category_tokens: dict[str, int] = defaultdict(int)
    for file_info in file_infos:
        category_counts[file_info.category.value] += 1
        category_tokens[file_info.category.value] += file_info.tokens

    filtered_by_category_files = scanner_files - len(file_infos)
    filtered_by_category_tokens = scanner_tokens - sum(file_info.tokens for file_info in file_infos)
    noise_summary = {
        "scanner_files": scanner_files,
        "scanner_tokens": scanner_tokens,
        "files_after_filters": len(file_infos),
        "tokens_after_filters": sum(file_info.tokens for file_info in file_infos),
        "filtered_by_category_files": filtered_by_category_files,
        "filtered_by_category_tokens": filtered_by_category_tokens,
        "file_reduction_ratio": round((filtered_by_category_files / scanner_files), 4) if scanner_files else 0.0,
        "token_reduction_ratio": round((filtered_by_category_tokens / scanner_tokens), 4) if scanner_tokens else 0.0,
        "scanner_category_counts": dict(scanner_category_counts),
        "scanner_category_tokens": dict(scanner_category_tokens),
    }

    tokens_after_filters = noise_summary["tokens_after_filters"]
    noise_tokens = category_tokens.get(FileCategory.OTHER.value, 0) + category_tokens.get(
        FileCategory.CONFIGURATION.value, 0
    )
    noise_ratio = (noise_tokens / tokens_after_filters) if tokens_after_filters else 0.0
    signal_score = {
        "value": round(max(0.0, min(100.0, (1.0 - noise_ratio) * 100.0)), 2),
        "scale": "0-100",
        "noise_tokens": noise_tokens,
        "actionable_tokens": tokens_after_filters - noise_tokens,
        "total_tokens": tokens_after_filters,
        "noise_ratio": round(noise_ratio, 4),
        "method": "100 * (1 - (other_tokens + configuration_tokens) / total_tokens_after_filters)",
    }

    totals["scanner_files"] = scanner_files
    totals["scanner_tokens"] = scanner_tokens
    totals["files"] = len(file_infos)
    totals["tokens"] = sum(file_info.tokens for file_info in file_infos)
    totals["analysis_scope"] = analysis_scope
    totals["category_counts"] = dict(category_counts)
    totals["category_tokens"] = dict(category_tokens)
    totals["noise_summary"] = noise_summary
    totals["signal_score"] = signal_score

    # Sort by tokens descending, take top N
    file_infos.sort(key=lambda f: f.tokens, reverse=True)
    dir_infos.sort(key=lambda d: d.tokens, reverse=True)

    return file_infos[:top_n], dir_infos[:top_n], totals
