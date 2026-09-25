from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.geo import geom_centroid_lonlat
from app.models.edges import Relationship
from app.models.events import Project, ProcurementNotice, Signal
from app.models.infrastructure import InfrastructureAsset, InfrastructureCluster, InfrastructureNetwork
from app.models.organisation import Organisation
from app.models.provenance import Claim, Evidence, Source

router = APIRouter(prefix="/api/infrastructures", tags=["infrastructures"])

_ENTITY_MODELS = {
    "asset": InfrastructureAsset,
    "cluster": InfrastructureCluster,
    "network": InfrastructureNetwork,
}


def _org_name(db: Session, org_id) -> str | None:
    if not org_id:
        return None
    org = db.get(Organisation, org_id)
    return org.legal_name if org else None


def _asset_summary(db: Session, asset: InfrastructureAsset) -> dict[str, Any]:
    lonlat = geom_centroid_lonlat(asset.geom)
    return {
        "id": str(asset.id),
        "kind": "asset",
        "canonical_name": asset.canonical_name,
        "category": asset.category,
        "subcategory": asset.subcategory,
        "country": asset.country,
        "status": asset.status,
        "lon": lonlat[0] if lonlat else None,
        "lat": lonlat[1] if lonlat else None,
        "geometry_precision": asset.geometry_precision,
        "sensitivity_level": asset.sensitivity_level,
        "operator": _org_name(db, asset.operator_org_id),
        "operator_id": str(asset.operator_org_id) if asset.operator_org_id else None,
        "owner": _org_name(db, asset.owner_org_id),
        "lares_fit": asset.lares_fit,
        "data_completeness_score": asset.data_completeness_score,
        "sales_readiness_state": asset.sales_readiness_state,
        "last_verified_at": asset.last_verified_at,
    }


def _cluster_summary(db: Session, cluster: InfrastructureCluster) -> dict[str, Any]:
    lonlat = geom_centroid_lonlat(cluster.geom)
    return {
        "id": str(cluster.id),
        "kind": "cluster",
        "canonical_name": cluster.canonical_name,
        "category": cluster.category,
        "subcategory": None,
        "country": cluster.country,
        "status": None,
        "lon": lonlat[0] if lonlat else None,
        "lat": lonlat[1] if lonlat else None,
        "geometry_precision": cluster.geometry_precision,
        "sensitivity_level": cluster.sensitivity_level,
        "operator": _org_name(db, cluster.authority_org_id),
        "operator_id": str(cluster.authority_org_id) if cluster.authority_org_id else None,
        "owner": None,
        "lares_fit": None,
        "data_completeness_score": None,
        "sales_readiness_state": None,
        "last_verified_at": None,
    }


def _network_summary(db: Session, network: InfrastructureNetwork) -> dict[str, Any]:
    lonlat = geom_centroid_lonlat(network.geom)
    return {
        "id": str(network.id),
        "kind": "network",
        "canonical_name": network.canonical_name,
        "category": network.category,
        "subcategory": None,
        "country": network.country,
        "status": None,
        "lon": lonlat[0] if lonlat else None,
        "lat": lonlat[1] if lonlat else None,
        "geometry_precision": network.geometry_precision,
        "sensitivity_level": network.sensitivity_level,
        "operator": _org_name(db, network.operator_org_id),
        "operator_id": str(network.operator_org_id) if network.operator_org_id else None,
        "owner": None,
        "lares_fit": None,
        "data_completeness_score": None,
        "sales_readiness_state": None,
        "last_verified_at": None,
    }


@router.get("")
def list_infrastructures(
    db: Session = Depends(get_db),
    country: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    q: str | None = None,
    min_lares_fit: int | None = None,
    kind: str | None = Query(None, description="asset|cluster|network; default: all"),
    limit: int = Query(200, le=1000),
    offset: int = 0,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    def matches_text(name: str) -> bool:
        return q is None or q.lower() in name.lower()

    if kind in (None, "asset"):
        stmt = select(InfrastructureAsset)
        if country:
            stmt = stmt.where(InfrastructureAsset.country == country)
        if category:
            stmt = stmt.where(InfrastructureAsset.category == category)
        if subcategory:
            stmt = stmt.where(InfrastructureAsset.subcategory == subcategory)
        if min_lares_fit is not None:
            stmt = stmt.where(InfrastructureAsset.lares_fit >= min_lares_fit)
        if q:
            stmt = stmt.where(InfrastructureAsset.canonical_name.ilike(f"%{q}%"))
        for asset in db.execute(stmt).scalars():
            results.append(_asset_summary(db, asset))

    if kind in (None, "cluster"):
        stmt = select(InfrastructureCluster)
        if country:
            stmt = stmt.where(InfrastructureCluster.country == country)
        if category:
            stmt = stmt.where(InfrastructureCluster.category == category)
        if q:
            stmt = stmt.where(InfrastructureCluster.canonical_name.ilike(f"%{q}%"))
        if not subcategory and not min_lares_fit:
            for cluster in db.execute(stmt).scalars():
                results.append(_cluster_summary(db, cluster))

    if kind in (None, "network"):
        stmt = select(InfrastructureNetwork)
        if country:
            stmt = stmt.where(InfrastructureNetwork.country == country)
        if category:
            stmt = stmt.where(InfrastructureNetwork.category == category)
        if q:
            stmt = stmt.where(InfrastructureNetwork.canonical_name.ilike(f"%{q}%"))
        if not subcategory and not min_lares_fit:
            for network in db.execute(stmt).scalars():
                results.append(_network_summary(db, network))

    total = len(results)
    page = results[offset : offset + limit]
    return {"total": total, "items": page}


@router.get("/{entity_id}")
def get_infrastructure_detail(entity_id: UUID, db: Session = Depends(get_db)) -> dict[str, Any]:
    for kind, model in _ENTITY_MODELS.items():
        entity = db.get(model, entity_id)
        if entity:
            return _build_detail(db, kind, entity)
    raise HTTPException(status_code=404, detail="Infrastructure not found")


def _build_detail(db: Session, kind: str, entity) -> dict[str, Any]:
    summary_fn = {"asset": _asset_summary, "cluster": _cluster_summary, "network": _network_summary}[kind]
    summary = summary_fn(db, entity)

    # organisation graph: operator -> owner -> ultimate parent ; public authority
    operator_id = getattr(entity, "operator_org_id", None) or getattr(entity, "authority_org_id", None)
    owner_id = getattr(entity, "owner_org_id", None)
    ultimate_owner_id = getattr(entity, "ultimate_owner_org_id", None)
    public_authority_id = getattr(entity, "public_authority_org_id", None)

    org_graph = []
    for role, org_id in [
        ("operator", operator_id),
        ("owner", owner_id),
        ("ultimate_parent", ultimate_owner_id),
        ("public_authority", public_authority_id),
    ]:
        if org_id:
            org = db.get(Organisation, org_id)
            if org:
                org_graph.append(
                    {
                        "role": role,
                        "organisation_id": str(org.id),
                        "legal_name": org.legal_name,
                        "org_type": org.org_type,
                        "hq_country": org.hq_country,
                        "website": org.website,
                    }
                )
                if org.direct_parent_id:
                    parent = db.get(Organisation, org.direct_parent_id)
                    if parent:
                        org_graph.append(
                            {
                                "role": f"{role}_direct_parent",
                                "organisation_id": str(parent.id),
                                "legal_name": parent.legal_name,
                                "org_type": parent.org_type,
                                "hq_country": parent.hq_country,
                                "website": parent.website,
                            }
                        )

    # relationships (both directions)
    rel_stmt = select(Relationship).where(
        or_(
            (Relationship.subject_type == kind_to_entity_type(kind)) & (Relationship.subject_id == entity.id),
            (Relationship.object_type == kind_to_entity_type(kind)) & (Relationship.object_id == entity.id),
        )
    )
    relationships = [
        {
            "predicate": r.predicate,
            "subject_type": r.subject_type,
            "subject_id": str(r.subject_id),
            "object_type": r.object_type,
            "object_id": str(r.object_id),
            "confidence": r.confidence,
            "verification_state": r.verification_state,
        }
        for r in db.execute(rel_stmt).scalars()
    ]

    # related infrastructure: other assets/clusters/networks with the same operator
    related = []
    if operator_id:
        for other_kind, model in _ENTITY_MODELS.items():
            op_field = "authority_org_id" if other_kind == "cluster" else "operator_org_id"
            if not hasattr(model, op_field):
                continue
            stmt = select(model).where(getattr(model, op_field) == operator_id, model.id != entity.id)
            for other in db.execute(stmt).scalars():
                related.append(
                    {
                        "id": str(other.id),
                        "kind": other_kind,
                        "canonical_name": other.canonical_name,
                        "country": other.country,
                    }
                )

    # evidence: claims about this entity
    claim_stmt = select(Claim).where(
        Claim.subject_type == kind_to_entity_type(kind), Claim.subject_id == entity.id
    )
    evidence = []
    for claim in db.execute(claim_stmt).scalars():
        for ev in db.execute(select(Evidence).where(Evidence.claim_id == claim.id)).scalars():
            source = db.get(Source, ev.source_id)
            evidence.append(
                {
                    "predicate": claim.predicate,
                    "object_literal": claim.object_literal,
                    "confidence": claim.confidence,
                    "verification_state": claim.verification_state,
                    "excerpt": ev.excerpt,
                    "extraction_method": ev.extraction_method,
                    "source_publisher": source.publisher if source else None,
                    "source_title": source.title if source else None,
                    "source_url": source.url if source else None,
                    "source_published_at": source.published_at if source else None,
                }
            )

    projects = [
        {"id": str(p.id), "name": p.name, "status": p.status, "announced_at": p.announced_at}
        for p in db.execute(
            select(Project).where(Project.infrastructure_asset_id == entity.id)
        ).scalars()
    ] if kind == "asset" else []

    procurement = [
        {"id": str(pn.id), "title": pn.title, "published_at": pn.published_at, "security_relevance_category": pn.security_relevance_category}
        for pn in db.execute(
            select(ProcurementNotice).where(ProcurementNotice.infrastructure_asset_id == entity.id)
        ).scalars()
    ] if kind == "asset" else []

    signals = [
        {"id": str(s.id), "signal_type": s.signal_type, "summary": s.summary, "event_date": s.event_date, "confidence": s.confidence}
        for s in db.execute(select(Signal).where(Signal.infrastructure_asset_id == entity.id)).scalars()
    ] if kind == "asset" else []

    relevance_breakdown = None
    if kind == "asset":
        relevance_breakdown = {
            "strategic_importance": entity.strategic_importance,
            "physical_complexity": entity.physical_complexity,
            "response_complexity": entity.response_complexity,
            "autonomous_fit": entity.autonomous_fit,
            "security_intensity": entity.security_intensity,
            "buyer_accessibility": entity.buyer_accessibility,
            "contactability": entity.contactability,
            "procurement_signal": entity.procurement_signal,
            "change_signal": entity.change_signal,
            "data_confidence": entity.data_confidence,
            "lares_fit": entity.lares_fit,
        }

    return {
        **summary,
        "operational_description": getattr(entity, "operational_description", None)
        or getattr(entity, "description", None),
        "organisation_graph": org_graph,
        "relationships": relationships,
        "related_infrastructure": related,
        "evidence": evidence,
        "projects": projects,
        "procurement": procurement,
        "signals": signals,
        "relevance_breakdown": relevance_breakdown,
    }


def kind_to_entity_type(kind: str) -> str:
    return {"asset": "infrastructure_asset", "cluster": "infrastructure_cluster", "network": "infrastructure_network"}[kind]
