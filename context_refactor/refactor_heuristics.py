"""Compatibility facade for the heuristics-based refactor engine."""

from __future__ import annotations

from . import refactor_heuristics_support as _support
from .refactor_heuristics_engine import HeuristicsEngine

_EXT_TO_LANGUAGE = _support._EXT_TO_LANGUAGE
_PRIORITY_RANK = _support._PRIORITY_RANK
_deduplicate = _support._deduplicate
_extract_problems = _support._extract_problems
_extract_suggestions = _support._extract_suggestions
_priority_rank = _support._priority_rank
_short_target = _support._short_target

__all__ = ["HeuristicsEngine"]
