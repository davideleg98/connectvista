from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.infrastructure import InfrastructureAsset, InfrastructureCluster, InfrastructureNetwork

router = APIRouter(prefix="/api/coverage", tags=["coverage"])


@router.get("")
def coverage_matrix(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Country x category matrix (spec §41) — candidates / with-operator /
    outreach-ready counts, so coverage is measurable rather than assumed."""
    cell = lambda: {"candidates": 0, "with_operator": 0, "outreach_ready": 0}
    matrix: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(cell))

    for asset in db.execute(select(InfrastructureAsset)).scalars():
        c = matrix[asset.country or "??"][asset.category]
        c["candidates"] += 1
        if asset.operator_org_id:
            c["with_operator"] += 1
        if asset.sales_readiness_state == "OUTREACH_READY":
            c["outreach_ready"] += 1

    for cluster in db.execute(select(InfrastructureCluster)).scalars():
        c = matrix[cluster.country or "??"][cluster.category]
        c["candidates"] += 1
        if cluster.authority_org_id:
            c["with_operator"] += 1

    for network in db.execute(select(InfrastructureNetwork)).scalars():
        c = matrix[network.country or "??"][network.category]
        c["candidates"] += 1
        if network.operator_org_id:
            c["with_operator"] += 1

    return {"matrix": {country: dict(cats) for country, cats in matrix.items()}}
