"""Context-budget computation.

Determines whether the project fits inside an LLM context window and
computes the overflow metrics.
"""

from __future__ import annotations

import math

from .models import ContextBudget


def compute_budget(
    total_tokens: int,
    total_files: int,
    llm_context_size: int = 128_000,
    safety_margin: float = 0.80,
) -> ContextBudget:
    """Compute context budget and overflow metrics.

    Parameters
    ----------
    total_tokens:
        Estimated token count for the whole project.
    total_files:
        Number of files scanned.
    llm_context_size:
        Maximum tokens the target LLM supports (e.g. 128000, 200000).
    safety_margin:
        Fraction of the context window to consider usable (0.0-1.0).
        The remaining space is reserved for the system prompt, user query,
        and the model's response.

    Returns
    -------
    ContextBudget
    """
    context_budget = math.floor(llm_context_size * safety_margin)
    overflow = max(0, total_tokens - context_budget)
    overflow_ratio = overflow / context_budget if context_budget > 0 else 0.0

    return ContextBudget(
        llm_context_size=llm_context_size,
        safety_margin=safety_margin,
        context_budget=context_budget,
        total_tokens=total_tokens,
        total_files=total_files,
        fits_context=total_tokens <= context_budget,
        overflow_tokens=overflow,
        overflow_ratio=overflow_ratio,
    )
