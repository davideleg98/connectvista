"""Claim/evidence recording helper shared by all adapters. See ONTOLOGY.md.

Every adapter calls `record_evidence` for the facts it writes so nothing is
published without "why do we believe this" attached (spec §10/§16, and
DATA_GOVERNANCE.md's publish gate).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.provenance import Claim, Evidence, Source


def get_or_create_source(db: Session, *, source_registry_id, publisher: str, title: str, url: str,
                          published_at: date | None = None, content_hash: str | None = None) -> Source:
    existing = None
    if content_hash:
        existing = db.query(Source).filter(Source.content_hash == content_hash).first()
    if existing:
        return existing
    src = Source(
        source_registry_id=source_registry_id,
        publisher=publisher,
        title=title,
        url=url,
        published_at=published_at,
        retrieved_at=datetime.utcnow(),
        content_hash=content_hash,
    )
    db.add(src)
    db.flush()
    return src


def record_evidence(
    db: Session,
    *,
    subject_type: str,
    subject_id,
    predicate: str,
    object_type: str | None = None,
    object_id=None,
    object_literal: str | None = None,
    confidence: int,
    verification_state: str,
    source: Source,
    excerpt: str | None = None,
    extraction_method: str = "deterministic_id_match",
) -> Claim:
    claim = Claim(
        subject_type=subject_type,
        subject_id=subject_id,
        predicate=predicate,
        object_type=object_type,
        object_id=object_id,
        object_literal=object_literal,
        confidence=confidence,
        verification_state=verification_state,
    )
    db.add(claim)
    db.flush()
    db.add(
        Evidence(
            claim_id=claim.id,
            source_id=source.id,
            excerpt=excerpt,
            extraction_method=extraction_method,
        )
    )
    return claim
