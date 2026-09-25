"""Sales-readiness lifecycle + publish gate. See ONTOLOGY.md and
DATA_GOVERNANCE.md "Provenance is mandatory, not optional".
"""

from __future__ import annotations

from app.models.enums import SalesReadinessState


def can_publish(*, claim_count: int) -> bool:
    """An asset with zero evidenced claims may not be published."""
    return claim_count > 0


def next_state(
    *,
    has_operator: bool,
    has_owner: bool,
    has_role_or_contact: bool,
    has_current_signal_or_procurement: bool,
    lares_fit: int,
) -> str:
    if not (has_operator or has_owner):
        return SalesReadinessState.NEEDS_ENRICHMENT.value
    if has_operator and has_owner and not has_role_or_contact:
        return SalesReadinessState.IDENTIFIED.value
    if has_operator and has_owner and has_role_or_contact and not has_current_signal_or_procurement:
        return SalesReadinessState.QUALIFIED.value
    if has_operator and has_owner and has_role_or_contact and has_current_signal_or_procurement and lares_fit >= 50:
        return SalesReadinessState.OUTREACH_READY.value
    return SalesReadinessState.QUALIFIED.value
