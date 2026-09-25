from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.geo import geom_centroid_lonlat
from app.models.infrastructure import InfrastructureAsset, InfrastructureCluster, InfrastructureNetwork

router = APIRouter(prefix="/api/map", tags=["map"])

_MODELS = [
    (InfrastructureAsset, "asset"),
    (InfrastructureCluster, "cluster"),
    (InfrastructureNetwork, "network"),
]


@router.get("/bbox")
def bbox_query(
    db: Session = Depends(get_db),
    min_lon: float = Query(-25.0),
    min_lat: float = Query(34.0),
    max_lon: float = Query(45.0),
    max_lat: float = Query(72.0),
    category: str | None = None,
    country: str | None = None,
    min_lares_fit: int | None = None,
) -> dict[str, Any]:
    """Server-side bbox query — never ships the full dataset to the browser
    (spec §23/§32). This is the interim implementation ahead of MVT tiles;
    see ARCHITECTURE.md "Deferred"."""
    features = []
    for model, kind in _MODELS:
        stmt = select(model).where(model.geom.isnot(None))
        if category:
            stmt = stmt.where(model.category == category)
        if country:
            stmt = stmt.where(model.country == country)
        if min_lares_fit is not None and hasattr(model, "lares_fit"):
            stmt = stmt.where(model.lares_fit >= min_lares_fit)
        elif min_lares_fit is not None:
            continue  # clusters/networks have no lares_fit yet — excluded by this filter, not silently included

        for entity in db.execute(stmt).scalars():
            lonlat = geom_centroid_lonlat(entity.geom)
            if not lonlat:
                continue
            lon, lat = lonlat
            if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
                continue
            features.append(
                {
                    "id": str(entity.id),
                    "kind": kind,
                    "canonical_name": entity.canonical_name,
                    "category": entity.category,
                    "country": entity.country,
                    "lon": lon,
                    "lat": lat,
                    "geometry_precision": entity.geometry_precision,
                    "lares_fit": getattr(entity, "lares_fit", None),
                }
            )
    return {"count": len(features), "features": features}
