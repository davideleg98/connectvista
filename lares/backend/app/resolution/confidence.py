"""Deterministic confidence scoring. See ONTOLOGY.md "Confidence model" —
explicit rules, never a bare LLM-guessed float.
"""

from __future__ import annotations

TIER_BASE_POINTS = {1: 70, 2: 55, 3: 40, 4: 25, 5: 10}


def base_score(tier: int) -> int:
    return TIER_BASE_POINTS.get(tier, 10)


def score_claim(
    *,
    tier: int,
    deterministic_id_match: bool = False,
    independent_corroborations: int = 0,
    contradicted_by_higher_tier: bool = False,
    months_since_seen: int = 0,
    volatile_predicate: bool = False,
) -> int:
    score = base_score(tier)
    if deterministic_id_match:
        score += 15
    score += min(independent_corroborations * 10, 20)
    if contradicted_by_higher_tier:
        score -= 20
    if volatile_predicate and months_since_seen > 18:
        score -= min(months_since_seen - 18, 40)
    return max(0, min(100, score))
