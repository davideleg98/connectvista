from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.events import ProcurementNotice, Signal
from app.models.infrastructure import InfrastructureAsset, InfrastructureCluster, InfrastructureNetwork
from app.models.organisation import Organisation

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def universal_search(q: str = Query(..., min_length=2), db: Session = Depends(get_db)) -> dict[str, Any]:
    like = f"%{q}%"
    infrastructures = []
    for model, kind in [
        (InfrastructureAsset, "asset"),
        (InfrastructureCluster, "cluster"),
        (InfrastructureNetwork, "network"),
    ]:
        for entity in db.execute(
            select(model).where(model.canonical_name.ilike(like)).limit(20)
        ).scalars():
            infrastructures.append(
                {"id": str(entity.id), "kind": kind, "canonical_name": entity.canonical_name, "country": entity.country}
            )

    organisations = [
        {"id": str(o.id), "legal_name": o.legal_name, "org_type": o.org_type, "hq_country": o.hq_country}
        for o in db.execute(select(Organisation).where(Organisation.legal_name.ilike(like)).limit(20)).scalars()
    ]

    procurement = [
        {"id": str(p.id), "title": p.title}
        for p in db.execute(select(ProcurementNotice).where(ProcurementNotice.title.ilike(like)).limit(20)).scalars()
    ]

    signals = [
        {"id": str(s.id), "summary": s.summary}
        for s in db.execute(select(Signal).where(Signal.summary.ilike(like)).limit(20)).scalars()
    ]

    return {
        "query": q,
        "infrastructures": infrastructures,
        "organisations": organisations,
        "procurement": procurement,
        "signals": signals,
    }
