"""Dependency module resolution helpers."""

from __future__ import annotations

import os
import sys

from .models import DependencyScope

_PYTHON_STDLIB_MODULES: frozenset[str] = frozenset(sys.stdlib_module_names)


def resolve_module_to_file(
    module_path: str,
    project_path: str,
    source_file: str,
    ext: str,
    symbol: str | None = None,
) -> tuple[str | None, DependencyScope]:
    """Resolve a module import to a project-relative file when possible."""
    if ext == ".py":
        return _resolve_python_module(module_path, project_path, source_file, symbol=symbol)
    if ext in {".ts", ".tsx", ".js", ".jsx"}:
        return _resolve_ts_module(module_path, project_path, source_file)
    return None, DependencyScope.EXTERNAL


def _resolve_python_module(
    module_path: str,
    project_path: str,
    source_file: str,
    symbol: str | None = None,
) -> tuple[str | None, DependencyScope]:
    """Resolve a Python module path to a project file."""
    if not module_path:
        return None, DependencyScope.EXTERNAL

    module_candidates: list[str] = []
    if symbol and symbol != "*":
        if module_path.endswith("."):
            module_candidates.append(f"{module_path}{symbol}")
        else:
            module_candidates.append(f"{module_path}.{symbol}")
    module_candidates.append(module_path)

    for candidate_module in module_candidates:
        if candidate_module.startswith("."):
            dots = len(candidate_module) - len(candidate_module.lstrip("."))
            remainder = candidate_module[dots:]
            source_dir = os.path.dirname(source_file)
            for _ in range(dots - 1):
                source_dir = os.path.dirname(source_dir)

            parts = remainder.split(".") if remainder else []
            base = os.path.join(project_path, source_dir, *parts)
            resolved = _check_python_path(base, project_path)
            if resolved[0] is not None:
                return resolved

        top_level = candidate_module.split(".")[0]
        if top_level in _PYTHON_STDLIB_MODULES:
            continue

        base = os.path.join(project_path, *candidate_module.split("."))
        resolved = _check_python_path(base, project_path)
        if resolved[0] is not None:
            return resolved

    return None, DependencyScope.EXTERNAL


def _check_python_path(
    base: str,
    project_path: str,
) -> tuple[str | None, DependencyScope]:
    """Check if *base*.py or *base*/__init__.py exists."""
    for candidate in (base + ".py", os.path.join(base, "__init__.py")):
        if os.path.isfile(candidate):
            return os.path.relpath(candidate, project_path), DependencyScope.INTERNAL
    return None, DependencyScope.EXTERNAL


def _resolve_ts_module(
    module_path: str,
    project_path: str,
    source_file: str,
) -> tuple[str | None, DependencyScope]:
    """Resolve a TypeScript/JavaScript module path."""
    if not module_path.startswith("."):
        return None, DependencyScope.EXTERNAL

    source_dir = os.path.dirname(os.path.join(project_path, source_file))
    base = os.path.normpath(os.path.join(source_dir, module_path))

    for suffix in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"):
        candidate = base + suffix
        if os.path.isfile(candidate):
            return os.path.relpath(candidate, project_path), DependencyScope.INTERNAL

    return None, DependencyScope.EXTERNAL
