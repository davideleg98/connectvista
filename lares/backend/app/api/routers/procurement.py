from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.events import ProcurementNotice
from app.models.organisation import Organisation

router = APIRouter(prefix="/api/procurement", tags=["procurement"])


@router.get("")
def list_procurement(
    db: Session = Depends(get_db),
    country: str | None = None,
    security_relevance_category: str | None = None,
    limit: int = Query(200, le=1000),
) -> dict[str, Any]:
    stmt = select(ProcurementNotice)
    if country:
        stmt = stmt.where(ProcurementNotice.country == country)
    if security_relevance_category:
        stmt = stmt.where(ProcurementNotice.security_relevance_category == security_relevance_category)
    rows = db.execute(stmt.limit(limit)).scalars().all()
    items = []
    for p in rows:
        authority = db.get(Organisation, p.contracting_authority_org_id) if p.contracting_authority_org_id else None
        items.append(
            {
                "id": str(p.id),
                "ted_notice_id": p.ted_notice_id,
                "title": p.title,
                "contracting_authority": authority.legal_name if authority else None,
                "country": p.country,
                "cpv_codes": p.cpv_codes,
                "security_relevance_category": p.security_relevance_category,
                "value_eur_estimate": p.value_eur_estimate,
                "published_at": p.published_at,
                "deadline_at": p.deadline_at,
            }
        )
    return {"total": len(items), "items": items}
