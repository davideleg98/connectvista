"""Human review of ambiguous entity-resolution matches. See ONTOLOGY.md /
spec §14 and §44 ("Merge Duplicate" as a first-class product action).

A pending item means the resolver created a *new* row rather than silently
merging into `matched_entity_id` — approving here confirms they're the same
entity and merges; rejecting confirms they're genuinely different and just
closes the item. Either way nothing was ever silently merged or dropped.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.edges import Relationship
from app.models.infrastructure import InfrastructureAsset
from app.models.ops import MergeLog
from app.models.organisation import Organisation
from app.models.provenance import Claim
from app.models.resolution import ReviewQueueItem

router = APIRouter(prefix="/api/review-queue", tags=["review-queue"])

_ENTITY_MODEL = {
    "organisation": Organisation,
    "infrastructure_asset": InfrastructureAsset,
}
_NAME_FIELD = {
    "organisation": "legal_name",
    "infrastructure_asset": "canonical_name",
}


def _display_name(db: Session, entity_type: str, entity_id) -> str | None:
    if entity_id is None:
        return None
    model = _ENTITY_MODEL.get(entity_type)
    if model is None:
        return None
    row = db.get(model, entity_id)
    if row is None:
        return None
    return getattr(row, _NAME_FIELD[entity_type], None)


@router.get("")
def list_review_queue(db: Session = Depends(get_db), status: str = "pending") -> dict[str, Any]:
    rows = db.execute(
        select(ReviewQueueItem)
        .where(ReviewQueueItem.status == status)
        .order_by(ReviewQueueItem.created_at.desc())
    ).scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "entity_type": r.entity_type,
                "status": r.status,
                "match_score": r.match_score,
                "match_signals": r.match_signals,
                "candidate_entity_id": str(r.created_entity_id) if r.created_entity_id else None,
                "candidate_name": _display_name(db, r.entity_type, r.created_entity_id),
                "matched_entity_id": str(r.matched_entity_id) if r.matched_entity_id else None,
                "matched_name": _display_name(db, r.entity_type, r.matched_entity_id),
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


@router.post("/{item_id}/approve")
def approve_merge(item_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Confirms the ambiguous candidate IS the matched entity: re-points every
    claim and relationship from the candidate onto the survivor, fills any
    fields the survivor is missing, records a MergeLog row (never deletes
    provenance), then removes the now-redundant candidate row."""
    item = db.get(ReviewQueueItem, item_id)
    if item is None or item.status != "pending":
        raise HTTPException(404, "No pending review item with that id")
    if item.created_entity_id is None or item.matched_entity_id is None:
        raise HTTPException(409, "Review item is missing entity references")

    model = _ENTITY_MODEL[item.entity_type]
    survivor = db.get(model, item.matched_entity_id)
    candidate = db.get(model, item.created_entity_id)
    if survivor is None or candidate is None:
        raise HTTPException(409, "Referenced entity no longer exists")

    for column in model.__table__.columns:
        if column.name in ("id", "created_at", "updated_at"):
            continue
        current = getattr(survivor, column.name)
        if current in (None, "", []):
            incoming = getattr(candidate, column.name)
            if incoming not in (None, "", []):
                setattr(survivor, column.name, incoming)

    for claim in db.execute(
        select(Claim).where(Claim.subject_type == item.entity_type, Claim.subject_id == candidate.id)
    ).scalars():
        claim.subject_id = survivor.id
    for claim in db.execute(
        select(Claim).where(Claim.object_type == item.entity_type, Claim.object_id == candidate.id)
    ).scalars():
        claim.object_id = survivor.id
    for rel in db.execute(
        select(Relationship).where(Relationship.subject_type == item.entity_type, Relationship.subject_id == candidate.id)
    ).scalars():
        rel.subject_id = survivor.id
    for rel in db.execute(
        select(Relationship).where(Relationship.object_type == item.entity_type, Relationship.object_id == candidate.id)
    ).scalars():
        rel.object_id = survivor.id

    db.add(
        MergeLog(
            entity_type=item.entity_type,
            surviving_id=survivor.id,
            merged_id=candidate.id,
            merge_reason="human-approved review-queue match",
            match_signals=item.match_signals,
            merged_by="review_queue_api",
        )
    )
    item.status = "approved"
    db.delete(candidate)
    db.commit()
    return {"status": "approved", "surviving_id": str(survivor.id)}


@router.post("/{item_id}/reject")
def reject_merge(item_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Confirms the candidate is a genuinely different entity: both rows
    stand as-is, the item is just closed."""
    item = db.get(ReviewQueueItem, item_id)
    if item is None or item.status != "pending":
        raise HTTPException(404, "No pending review item with that id")
    item.status = "rejected"
    db.commit()
    return {"status": "rejected"}
