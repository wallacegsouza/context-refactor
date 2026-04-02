"""Compatibility facade for dependency analysis helpers."""

from __future__ import annotations

from .dependency_graph_builder import build_dependency_graph
from .dependency_resolution import resolve_module_to_file as _resolve_module_to_file
from .dependency_weighting import compute_dependency_weights

__all__ = [
    "_resolve_module_to_file",
    "build_dependency_graph",
    "compute_dependency_weights",
]
