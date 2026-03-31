"""Refactor planner — produces ordered, grouped step-by-step plans.

Takes raw :class:`RefactorRecommendation` items and groups them into
cohesive *steps* that can be executed in sequence.  The ordering follows
a fixed priority ladder:

1. Split large Markdown documentation
2. Extract modules from God Files
3. Extract Methods / Classes from oversized constructs
4. Move / reorganise duplicated logic
5. Minor parameter-list and nesting improvements
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from .models import (
    ContextBudget,
    RefactorPlan,
    RefactorRecommendation,
    RefactorStep,
    RefactorTechnique,
)

# ── Ordering ladder ──────────────────────────────────────────────────────────

_TECHNIQUE_ORDER: dict[RefactorTechnique, int] = {
    RefactorTechnique.SPLIT_DOCUMENT: 0,
    RefactorTechnique.EXTRACT_MODULE: 1,
    RefactorTechnique.INVERT_DEPENDENCY: 2,
    RefactorTechnique.INTRODUCE_INTERFACE: 2,
    RefactorTechnique.EXTRACT_CLASS: 2,
    RefactorTechnique.EXTRACT_METHOD: 3,
    RefactorTechnique.MOVE_METHOD: 4,
    RefactorTechnique.MOVE_FIELD: 4,
    RefactorTechnique.DECOMPOSE_CONDITIONAL: 5,
    RefactorTechnique.EXTRACT_VARIABLE: 6,
    RefactorTechnique.REPLACE_TEMP_WITH_QUERY: 6,
    RefactorTechnique.RENAME_METHOD: 7,
}

_STEP_TITLES: dict[int, str] = {
    0: "Split large Markdown documentation into topic modules",
    1: "Extract modules from oversized God Files",
    2: "Reduce coupling and extract clearer seams",
    3: "Extract Methods from long functions",
    4: "Move duplicated logic into shared utilities",
    5: "Flatten deeply nested conditionals",
    6: "Simplify parameter lists and temporary variables",
    7: "Rename methods for clarity",
}


# ── Public API ───────────────────────────────────────────────────────────────


def generate_refactor_plan(
    recommendations: Sequence[RefactorRecommendation],
    budget: ContextBudget,
) -> RefactorPlan:
    """Build an ordered :class:`RefactorPlan` from raw recommendations.

    Parameters
    ----------
    recommendations:
        Output of :func:`refactor_engine.detect_refactor_candidates`.
    budget:
        The context budget computed earlier; used to project post-refactor fit.

    Returns
    -------
    RefactorPlan
    """
    if not recommendations:
        return RefactorPlan(
            steps=[],
            total_estimated_token_reduction=0,
            projected_tokens_after=budget.total_tokens,
            fits_context_after=budget.fits_context,
        )

    # Group by technique-order bucket
    buckets: dict[int, list[RefactorRecommendation]] = defaultdict(list)
    for rec in recommendations:
        order = _TECHNIQUE_ORDER.get(rec.technique, 99)
        buckets[order].append(rec)

    steps: list[RefactorStep] = []

    for step_number, order_key in enumerate(sorted(buckets), start=1):
        recs = buckets[order_key]

        # Collect unique affected files and techniques
        affected: list[str] = sorted({r.file_path for r in recs})
        techniques: list[RefactorTechnique] = sorted(
            {r.technique for r in recs}, key=lambda t: t.value
        )
        est_reduction = sum(r.estimated_token_reduction for r in recs)

        # Build description from individual recommendations
        desc_parts: list[str] = []
        for r in recs[:10]:  # Cap to keep plans readable
            desc_parts.append(f"• {r.description}")
        if len(recs) > 10:
            desc_parts.append(f"  … and {len(recs) - 10} more recommendations")

        title = _STEP_TITLES.get(order_key, f"Apply {techniques[0].value}")

        steps.append(
            RefactorStep(
                step_number=step_number,
                title=title,
                description="\n".join(desc_parts),
                affected_files=affected,
                techniques=techniques,
                estimated_token_reduction=est_reduction,
            )
        )

    total_reduction = sum(s.estimated_token_reduction for s in steps)
    projected_after = max(0, budget.total_tokens - total_reduction)

    return RefactorPlan(
        steps=steps,
        total_estimated_token_reduction=total_reduction,
        projected_tokens_after=projected_after,
        fits_context_after=projected_after <= budget.context_budget,
    )
