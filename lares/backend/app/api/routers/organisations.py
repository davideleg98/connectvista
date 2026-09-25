from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.geo import geom_centroid_lonlat
from app.models.infrastructure import InfrastructureAsset, InfrastructureCluster, InfrastructureNetwork
from app.models.organisation import Organisation
from app.models.people import Role

router = APIRouter(prefix="/api/organisations", tags=["organisations"])


def _summary(org: Organisation) -> dict[str, Any]:
    return {
        "id": str(org.id),
        "legal_name": org.legal_name,
        "trading_names": org.trading_names,
        "org_type": org.org_type,
        "hq_country": org.hq_country,
        "hq_city": org.hq_city,
        "website": org.website,
        "ownership_class": org.ownership_class,
        "lei": org.lei,
    }


@router.get("")
def list_organisations(
    db: Session = Depends(get_db),
    country: str | None = None,
    org_type: str | None = None,
    q: str | None = None,
    limit: int = Query(200, le=1000),
    offset: int = 0,
) -> dict[str, Any]:
    stmt = select(Organisation)
    if country:
        stmt = stmt.where(Organisation.hq_country == country)
    if org_type:
        stmt = stmt.where(Organisation.org_type == org_type)
    if q:
        stmt = stmt.where(Organisation.legal_name.ilike(f"%{q}%"))
    rows = db.execute(stmt.offset(offset).limit(limit)).scalars().all()
    total = db.execute(stmt).scalars().all()
    return {"total": len(total), "items": [_summary(o) for o in rows]}


@router.get("/{org_id}")
def get_organisation_detail(org_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    org = db.get(Organisation, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    portfolio: list[dict[str, Any]] = []
    for model, field, kind in [
        (InfrastructureAsset, "operator_org_id", "asset"),
        (InfrastructureAsset, "owner_org_id", "owned_asset"),
        (InfrastructureCluster, "authority_org_id", "cluster"),
        (InfrastructureNetwork, "operator_org_id", "network"),
    ]:
        for entity in db.execute(select(model).where(getattr(model, field) == org_id)).scalars():
            lonlat = geom_centroid_lonlat(entity.geom)
            portfolio.append(
                {
                    "id": str(entity.id),
                    "kind": kind,
                    "canonical_name": entity.canonical_name,
                    "country": entity.country,
                    "category": entity.category,
                    "lon": lonlat[0] if lonlat else None,
                    "lat": lonlat[1] if lonlat else None,
                }
            )

    subsidiaries = [
        _summary(o) for o in db.execute(select(Organisation).where(Organisation.direct_parent_id == org_id)).scalars()
    ]
    direct_parent = _summary(db.get(Organisation, org.direct_parent_id)) if org.direct_parent_id else None
    ultimate_parent = (
        _summary(db.get(Organisation, org.ultimate_parent_id)) if org.ultimate_parent_id else None
    )

    roles = [
        {"id": str(r.id), "role_category": r.role_category, "title_as_seen": r.title_as_seen, "is_filled": r.is_filled}
        for r in db.execute(select(Role).where(Role.organisation_id == org_id)).scalars()
    ]

    countries_covered = sorted({p["country"] for p in portfolio if p["country"]})

    return {
        **_summary(org),
        "legal_form": org.legal_form,
        "company_number": org.company_number,
        "jurisdiction": org.jurisdiction,
        "revenue_eur_estimate": org.revenue_eur_estimate,
        "employee_estimate": org.employee_estimate,
        "last_verified_at": org.last_verified_at,
        "direct_parent": direct_parent,
        "ultimate_parent": ultimate_parent,
        "subsidiaries": subsidiaries,
        "infrastructure_portfolio": portfolio,
        "countries_covered": countries_covered,
        "roles": roles,
    }
