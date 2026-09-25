from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.registry import IngestionRun, SourceRegistry

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
def list_sources(db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.execute(select(SourceRegistry)).scalars().all()
    return {
        "items": [
            {
                "id": str(s.id),
                "name": s.name,
                "tier": s.tier,
                "root_domain": s.root_domain,
                "data_categories": s.data_categories,
                "geography": s.geography,
                "access_method": s.access_method,
                "update_cadence": s.update_cadence,
                "requires_auth": s.requires_auth,
                "licence_status": s.licence_status,
                "attribution_required": s.attribution_required,
                "attribution_text": s.attribution_text,
                "enabled": s.enabled,
                "last_successful_run_at": s.last_successful_run_at,
                "last_failure_at": s.last_failure_at,
                "reliability_score": s.reliability_score,
            }
            for s in rows
        ]
    }


@router.get("/ingestion-runs")
def list_ingestion_runs(db: Session = Depends(get_db), limit: int = 100) -> dict[str, Any]:
    rows = db.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(limit)).scalars().all()
    return {
        "items": [
            {
                "id": str(r.id),
                "source_registry_id": str(r.source_registry_id),
                "started_at": r.started_at,
                "finished_at": r.finished_at,
                "status": r.status,
                "records_fetched": r.records_fetched,
                "records_created": r.records_created,
                "records_updated": r.records_updated,
                "records_rejected": r.records_rejected,
                "errors": r.errors,
            }
            for r in rows
        ]
    }
