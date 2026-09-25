"""Lares relevance model. See ONTOLOGY.md — ten explicit component scores,
never a hidden magic number. Weights and rationale are returned alongside
the score so the API/UI can show them (spec §19).

This is a first, honest, rule-based pass: every component is derived from
facts actually on the record (category, whether an operator/owner/signal/
procurement/contact is linked, evidence confidence) — never invented. A
component with no supporting evidence yet scores low/zero and stays that
way until real enrichment (signals, procurement, contacts) is ingested.
"""

from __future__ import annotations

from dataclasses import dataclass

# Category -> (strategic_importance, physical_complexity, autonomous_fit) baseline,
# derived from generally-known operational characteristics of the category
# (spec §19: "based on general operational characteristics, not discovered
# vulnerabilities"). Deliberately coarse; refined per-asset as real evidence
# (capacity, footprint, zone count) is ingested.
CATEGORY_BASELINE = {
    "energy": (80, 60, 55),
    "maritime": (85, 90, 75),
    "aviation": (80, 85, 65),
    "digital": (70, 40, 35),
    "rail": (65, 70, 50),
    "industrial": (55, 65, 60),
    "water": (60, 55, 40),
    "space": (70, 50, 60),
    "government": (50, 40, 30),
    "other": (40, 40, 30),
}

WEIGHTS = {
    "strategic_importance": 0.15,
    "physical_complexity": 0.10,
    "response_complexity": 0.10,
    "autonomous_fit": 0.10,
    "security_intensity": 0.10,
    "buyer_accessibility": 0.10,
    "contactability": 0.10,
    "procurement_signal": 0.10,
    "change_signal": 0.10,
    "data_confidence": 0.05,
}


@dataclass
class RelevanceInput:
    category: str
    has_operator: bool
    has_owner: bool
    has_public_authority: bool
    open_signal_count: int
    open_procurement_count: int
    contactable_role_count: int
    avg_claim_confidence: int  # 0-100


@dataclass
class RelevanceResult:
    components: dict[str, int]
    weights: dict[str, float]
    lares_fit: int


def compute_relevance(inp: RelevanceInput) -> RelevanceResult:
    strategic, physical, autonomous = CATEGORY_BASELINE.get(inp.category, CATEGORY_BASELINE["other"])

    response_complexity = min(100, physical + (10 if inp.has_operator and inp.has_owner else 0))
    security_intensity = min(100, 20 + inp.open_signal_count * 15)
    buyer_accessibility = (40 if inp.has_operator else 0) + (30 if inp.has_owner else 0) + (
        30 if inp.has_public_authority else 0
    )
    contactability = min(100, inp.contactable_role_count * 25)
    procurement_signal = min(100, inp.open_procurement_count * 30)
    change_signal = min(100, inp.open_signal_count * 25)
    data_confidence = inp.avg_claim_confidence

    components = {
        "strategic_importance": strategic,
        "physical_complexity": physical,
        "response_complexity": response_complexity,
        "autonomous_fit": autonomous,
        "security_intensity": security_intensity,
        "buyer_accessibility": buyer_accessibility,
        "contactability": contactability,
        "procurement_signal": procurement_signal,
        "change_signal": change_signal,
        "data_confidence": data_confidence,
    }
    lares_fit = round(sum(components[k] * WEIGHTS[k] for k in WEIGHTS))
    return RelevanceResult(components=components, weights=WEIGHTS, lares_fit=lares_fit)
