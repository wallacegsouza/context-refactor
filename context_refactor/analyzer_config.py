"""Analysis scope and dependency option resolution helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import FileCategory

DEFAULT_CONFIG_FILENAME = ".context-refactor.json"
REPORT_SCHEMA_VERSION = 2
DEPENDENCY_METRICS_VERSION = 1
DEFAULT_DEPENDENCY_MODE = "off"
DEFAULT_DEPENDENCY_MAX_DEPTH = 3
DEFAULT_DEPENDENCY_MAX_MULTIPLIER = 5.0
DEFAULT_DEPENDENCY_BASE_WEIGHT = 1.0
DEFAULT_DEPENDENCY_DEPTH_DECAY = 0.5
DEFAULT_DEPENDENCY_INTERNAL_WEIGHT = 1.0
DEFAULT_DEPENDENCY_EXTERNAL_WEIGHT = 0.7
DEFAULT_DEPENDENCY_FAN_IN_WEIGHT = 0.15
DEFAULT_DEPENDENCY_CYCLE_PENALTY = 0.10
VALID_DEPENDENCY_MODES = {"off", "report_only", "blended", "weighted"}
NOISE_REDUCTION_DIRS: list[str] = [
    "coverage",
    "lcov-report",
    "reports",
    "token-report",
]
NOISE_REDUCTION_GLOBS: list[str] = [
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.snap",
]
NOISE_REDUCTION_FILES: list[str] = [
    "lint.result.txt",
]
PROFILE_DEFAULTS: dict[str, dict[str, list[str]]] = {
    "default": {
        "exclude_dirs": NOISE_REDUCTION_DIRS,
        "exclude_globs": NOISE_REDUCTION_GLOBS,
        "exclude_files": NOISE_REDUCTION_FILES,
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
        "exclude_dirs": NOISE_REDUCTION_DIRS,
        "exclude_globs": NOISE_REDUCTION_GLOBS,
        "exclude_files": NOISE_REDUCTION_FILES,
        "include_categories": [FileCategory.SOURCE_CODE.value],
        "exclude_categories": [],
    },
    "docs": {
        "exclude_dirs": NOISE_REDUCTION_DIRS,
        "exclude_globs": NOISE_REDUCTION_GLOBS,
        "exclude_files": NOISE_REDUCTION_FILES,
        "include_categories": [FileCategory.MARKDOWN.value],
        "exclude_categories": [],
    },
}
VALID_CATEGORY_VALUES = {category.value for category in FileCategory}


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return split_csv(value)
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


def normalize_float_list(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, str):
        items = split_csv(value)
    elif isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
    else:
        raise ValueError(
            f"Expected string or list for dependency option, got {type(value).__name__}"
        )

    normalized: list[float] = []
    for item in items:
        normalized.append(float(item))
    return normalized


def merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


def normalize_categories(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        candidate = value.strip().lower()
        if not candidate:
            continue
        if candidate not in VALID_CATEGORY_VALUES:
            raise ValueError(
                "Unknown category "
                f"'{value}'. Valid values: {', '.join(sorted(VALID_CATEGORY_VALUES))}"
            )
        normalized.append(candidate)
    return merge_unique(normalized)


def load_project_config(
    project_path: str,
    config_path: str | None = None,
) -> tuple[dict[str, Any], str | None]:
    candidate = Path(config_path).resolve() if config_path else Path(project_path) / DEFAULT_CONFIG_FILENAME
    if not candidate.is_file():
        return {}, None

    with candidate.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("ContextRefactor config must be a JSON object")

    return data, str(candidate)


def load_analysis_config(
    project_path: str,
    config_path: str | None = None,
) -> tuple[dict[str, Any], str | None]:
    data, resolved_path = load_project_config(project_path, config_path=config_path)

    if isinstance(data.get("analysis"), dict):
        data = data["analysis"]

    return data, resolved_path


def resolve_analysis_scope(
    project_path: str,
    analysis_profile: str,
    config_path: str | None,
    exclude_dirs: list[str] | None,
    exclude_globs: list[str] | None,
    exclude_files: list[str] | None,
    include_categories: list[str] | None,
    exclude_categories: list[str] | None,
) -> dict[str, Any]:
    config, resolved_config_path = load_analysis_config(project_path, config_path=config_path)
    requested_profile = (analysis_profile or "default").strip().lower()
    if requested_profile and requested_profile != "default":
        profile = requested_profile
    else:
        profile = str(config.get("analysis_profile", requested_profile)).strip().lower()
    if profile not in PROFILE_DEFAULTS:
        raise ValueError(
            f"Unknown analysis profile '{profile}'. Valid profiles: {', '.join(sorted(PROFILE_DEFAULTS))}"
        )

    profile_defaults = PROFILE_DEFAULTS[profile]
    config_exclude_dirs = normalize_list(config.get("exclude_dirs"))
    config_exclude_globs = normalize_list(config.get("exclude_globs"))
    config_exclude_files = normalize_list(config.get("exclude_files"))
    config_include_categories = normalize_categories(normalize_list(config.get("include_categories")))
    config_exclude_categories = normalize_categories(normalize_list(config.get("exclude_categories")))

    resolved_include_categories = normalize_categories(
        merge_unique(
            profile_defaults.get("include_categories", []),
            config_include_categories,
            normalize_list(include_categories),
        )
    )
    resolved_exclude_categories = normalize_categories(
        merge_unique(
            profile_defaults.get("exclude_categories", []),
            config_exclude_categories,
            normalize_list(exclude_categories),
        )
    )

    return {
        "profile": profile,
        "config_path": resolved_config_path,
        "exclude_dirs": merge_unique(
            profile_defaults.get("exclude_dirs", []),
            config_exclude_dirs,
            normalize_list(exclude_dirs),
        ),
        "exclude_globs": merge_unique(
            profile_defaults.get("exclude_globs", []),
            config_exclude_globs,
            normalize_list(exclude_globs),
        ),
        "exclude_files": merge_unique(
            profile_defaults.get("exclude_files", []),
            config_exclude_files,
            normalize_list(exclude_files),
        ),
        "include_categories": resolved_include_categories,
        "exclude_categories": resolved_exclude_categories,
    }


def resolve_dependency_options(
    project_path: str,
    config_path: str | None,
    dependency_mode: str | None,
    dependency_max_depth: int | None,
    dependency_max_multiplier: float | None,
    dependency_base_weight: float | None,
    dependency_depth_decay: float | None,
    dependency_depth_weights: list[float] | None,
) -> dict[str, Any]:
    project_config, resolved_config_path = load_project_config(project_path, config_path=config_path)
    config = project_config.get("dependency_analysis", {})
    if config and not isinstance(config, dict):
        raise ValueError("dependency_analysis config must be a JSON object")

    requested_mode = (dependency_mode or "").strip().lower()
    if requested_mode:
        mode = requested_mode
    else:
        configured_mode = str(config.get("mode", "")).strip().lower()
        enabled_flag = config.get("enabled")
        if configured_mode:
            mode = configured_mode
        elif enabled_flag is True:
            mode = "report_only"
        else:
            mode = DEFAULT_DEPENDENCY_MODE

    if mode not in VALID_DEPENDENCY_MODES:
        raise ValueError(
            "Unknown dependency mode "
            f"'{mode}'. Valid values: {', '.join(sorted(VALID_DEPENDENCY_MODES))}"
        )

    configured_scope_weights = config.get("scope_weights", {})
    if configured_scope_weights and not isinstance(configured_scope_weights, dict):
        raise ValueError("dependency_analysis.scope_weights must be a JSON object")

    configured_depth_weights = normalize_float_list(config.get("depth_weights"))
    resolved_depth_weights = (
        dependency_depth_weights
        if dependency_depth_weights is not None
        else configured_depth_weights
    )

    return {
        "enabled": mode != "off",
        "mode": mode,
        "config_path": resolved_config_path,
        "max_depth": (
            dependency_max_depth
            if dependency_max_depth is not None
            else int(config.get("max_depth", DEFAULT_DEPENDENCY_MAX_DEPTH))
        ),
        "max_multiplier": (
            dependency_max_multiplier
            if dependency_max_multiplier is not None
            else float(config.get("max_multiplier", DEFAULT_DEPENDENCY_MAX_MULTIPLIER))
        ),
        "base_weight": (
            dependency_base_weight
            if dependency_base_weight is not None
            else float(config.get("base_weight", DEFAULT_DEPENDENCY_BASE_WEIGHT))
        ),
        "depth_decay": (
            dependency_depth_decay
            if dependency_depth_decay is not None
            else float(config.get("depth_decay", DEFAULT_DEPENDENCY_DEPTH_DECAY))
        ),
        "depth_weights": resolved_depth_weights or [],
        "internal_dependency_weight": float(
            configured_scope_weights.get("project_internal", DEFAULT_DEPENDENCY_INTERNAL_WEIGHT)
        ),
        "external_dependency_weight": float(
            configured_scope_weights.get("project_external", DEFAULT_DEPENDENCY_EXTERNAL_WEIGHT)
        ),
        "fan_in_weight": float(config.get("fan_in_weight", DEFAULT_DEPENDENCY_FAN_IN_WEIGHT)),
        "cycle_penalty": float(config.get("cycle_penalty", DEFAULT_DEPENDENCY_CYCLE_PENALTY)),
    }
