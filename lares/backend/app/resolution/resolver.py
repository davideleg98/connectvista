"""Entity resolution pipeline. See ONTOLOGY.md / spec §14.

Order of matching, strongest first:
1. Deterministic ID (LEI, company_number+jurisdiction, osm_id, facility_code,
   ted_notice_id) — an exact match here is a merge, no ambiguity.
2. Normalised-name + country fuzzy match (pg_trgm) above a high-confidence
   threshold — treated as a match.
3. A fuzzy match in the ambiguous band — NOT auto-merged. A new record is
   created (never dropped) and a ReviewQueueItem is logged so a human (or a
   later, more informed pass) can confirm the merge. See MergeLog for how a
   confirmed merge is applied without destroying history.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.infrastructure import InfrastructureAsset
from app.models.organisation import Organisation
from app.models.resolution import ReviewQueueItem

HIGH_CONFIDENCE_SIMILARITY = 0.82
AMBIGUOUS_FLOOR_SIMILARITY = 0.55

_LEGAL_SUFFIXES = re.compile(
    r"\b(s\.?p\.?a\.?|s\.?r\.?l\.?|s\.?a\.?|n\.?v\.?|b\.?v\.?|ag|gmbh|plc|ltd|inc|oy|as|asa|"
    r"sp[oó]lka|sepe|sh\.?p\.?k\.?)\b\.?",
    re.IGNORECASE,
)


def normalise_name(name: str) -> str:
    name = name.strip().lower()
    name = _LEGAL_SUFFIXES.sub("", name)
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def resolve_organisation(db: Session, natural_key: dict[str, Any], fields: dict[str, Any]) -> tuple[str, bool]:
    # natural_key fields (lei, company_number...) belong on the entity too —
    # merge them in (fields wins on overlap) so a freshly-created record
    # actually carries its deterministic id.
    fields = {**natural_key, **fields}

    # 1. deterministic ID match
    lei = natural_key.get("lei")
    if lei:
        existing = db.execute(select(Organisation).where(Organisation.lei == lei)).scalar_one_or_none()
        if existing:
            _merge_fields(existing, fields)
            db.flush()
            return str(existing.id), False

    company_number = natural_key.get("company_number")
    jurisdiction = natural_key.get("jurisdiction") or fields.get("jurisdiction")
    if company_number and jurisdiction:
        existing = db.execute(
            select(Organisation).where(
                Organisation.company_number == company_number,
                Organisation.jurisdiction == jurisdiction,
            )
        ).scalar_one_or_none()
        if existing:
            _merge_fields(existing, fields)
            db.flush()
            return str(existing.id), False

    # 2/3. fuzzy name match, scoped by country when known
    name = fields.get("legal_name") or natural_key.get("legal_name")
    if name:
        norm = normalise_name(name)
        query = select(
            Organisation.id,
            func.similarity(func.lower(Organisation.legal_name), norm).label("score"),
        ).order_by(func.similarity(func.lower(Organisation.legal_name), norm).desc()).limit(1)
        country = fields.get("hq_country")
        if country:
            query = query.where(Organisation.hq_country == country)
        row = db.execute(query).first()
        if row and row.score is not None:
            if row.score >= HIGH_CONFIDENCE_SIMILARITY:
                existing = db.get(Organisation, row.id)
                _merge_fields(existing, fields)
                db.flush()
                return str(existing.id), False
            if row.score >= AMBIGUOUS_FLOOR_SIMILARITY:
                created_id = _create_organisation(db, fields)
                db.add(
                    ReviewQueueItem(
                        entity_type="organisation",
                        candidate_natural_key=natural_key,
                        candidate_fields=fields,
                        matched_entity_id=row.id,
                        match_score=int(row.score * 100),
                        match_signals={"method": "trigram_name_similarity", "score": float(row.score)},
                    )
                )
                db.flush()
                return created_id, True

    return _create_organisation(db, fields), True


def resolve_infrastructure_asset(
    db: Session, natural_key: dict[str, Any], fields: dict[str, Any]
) -> tuple[str, bool]:
    fields = {**natural_key, **fields}
    osm_id = natural_key.get("osm_id")
    if osm_id:
        existing = db.execute(
            select(InfrastructureAsset).where(InfrastructureAsset.osm_id == str(osm_id))
        ).scalar_one_or_none()
        if existing:
            _merge_fields(existing, fields)
            db.flush()
            return str(existing.id), False

    facility_code = natural_key.get("facility_code")
    if facility_code:
        existing = db.execute(
            select(InfrastructureAsset).where(InfrastructureAsset.facility_code == facility_code)
        ).scalar_one_or_none()
        if existing:
            _merge_fields(existing, fields)
            db.flush()
            return str(existing.id), False

    name = fields.get("canonical_name") or natural_key.get("canonical_name")
    country = fields.get("country")
    if name and country:
        norm = normalise_name(name)
        query = (
            select(
                InfrastructureAsset.id,
                func.similarity(func.lower(InfrastructureAsset.canonical_name), norm).label("score"),
            )
            .where(InfrastructureAsset.country == country)
            .order_by(func.similarity(func.lower(InfrastructureAsset.canonical_name), norm).desc())
            .limit(1)
        )
        row = db.execute(query).first()
        if row and row.score is not None:
            if row.score >= HIGH_CONFIDENCE_SIMILARITY:
                existing = db.get(InfrastructureAsset, row.id)
                _merge_fields(existing, fields)
                db.flush()
                return str(existing.id), False
            if row.score >= AMBIGUOUS_FLOOR_SIMILARITY:
                created_id = _create_asset(db, fields)
                db.add(
                    ReviewQueueItem(
                        entity_type="infrastructure_asset",
                        candidate_natural_key=natural_key,
                        candidate_fields=fields,
                        matched_entity_id=row.id,
                        match_score=int(row.score * 100),
                        match_signals={"method": "trigram_name_similarity", "score": float(row.score)},
                    )
                )
                db.flush()
                return created_id, True

    return _create_asset(db, fields), True


def _merge_fields(entity, fields: dict[str, Any]) -> None:
    """Fill in nulls only — never silently overwrite an existing value with a
    lower-authority one. Overwriting is the caller's job via explicit claims."""
    for key, value in fields.items():
        if value is None or not hasattr(entity, key):
            continue
        if getattr(entity, key) in (None, "", []):
            setattr(entity, key, value)


def _create_organisation(db: Session, fields: dict[str, Any]) -> str:
    valid = {k: v for k, v in fields.items() if hasattr(Organisation, k)}
    org = Organisation(**valid)
    db.add(org)
    db.flush()
    return str(org.id)


def _create_asset(db: Session, fields: dict[str, Any]) -> str:
    valid = {k: v for k, v in fields.items() if hasattr(InfrastructureAsset, k)}
    asset = InfrastructureAsset(**valid)
    db.add(asset)
    db.flush()
    return str(asset.id)
