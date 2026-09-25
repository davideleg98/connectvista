"""GLEIF API v1 adapter — corporate ownership (LEI + Level 2 direct-parent
relationships). Tier 1/2, licence: cleared (GLEIF data is CC0). See
lares/SOURCES.md.

Real endpoints (documented, used by fetch() when egress is available):
  https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]={name}
  https://api.gleif.org/api/v1/lei-records/{lei}/direct-parent

Blocked in this sandbox (api.gleif.org not in the egress allowlist) — see
ARCHITECTURE.md. fetch() raises EgressBlockedError rather than pretending to
succeed; run() records that against the IngestionRun. Offline fixture at
tests/fixtures/gleif/terna_lei_record.json for adapter-logic tests.
"""

from __future__ import annotations

from typing import Any, Iterable

import httpx
from sqlalchemy.orm import Session

from app.adapters.base import EgressBlockedError, NormalisedRecord, SourceAdapter
from app.resolution.provenance import get_or_create_source, record_evidence
from app.resolution.resolver import resolve_organisation

GLEIF_BASE_URL = "https://api.gleif.org/api/v1"


class GleifAdapter(SourceAdapter):
    name = "gleif"

    def discover(self, legal_names: list[str] | None = None) -> Iterable[dict]:
        for legal_name in legal_names or []:
            yield {"legal_name": legal_name}

    def fetch(self, item: dict) -> dict:
        url = f"{GLEIF_BASE_URL}/lei-records"
        params = {"filter[entity.legalName]": item["legal_name"], "page[size]": 5}
        try:
            resp = httpx.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise EgressBlockedError(f"gleif fetch failed for {item['legal_name']!r}: {e}") from e

    def parse(self, raw: dict) -> Iterable[dict]:
        yield from raw.get("data", [])

    def normalise(self, parsed: dict) -> NormalisedRecord:
        attrs = parsed.get("attributes", {})
        entity = attrs.get("entity", {})
        legal_address = entity.get("legalAddress", {})
        lei = attrs.get("lei")
        legal_name = entity.get("legalName", {}).get("name")
        return NormalisedRecord(
            entity_type="organisation",
            natural_key={"lei": lei},
            fields={
                "legal_name": legal_name,
                "org_type": "other",
                "jurisdiction": legal_address.get("country"),
                "hq_country": legal_address.get("country"),
                "hq_city": legal_address.get("city"),
                "legal_form": entity.get("legalForm", {}).get("id"),
            },
            source_meta={
                "publisher": "GLEIF",
                "title": f"GLEIF LEI record {lei}",
                "url": f"https://www.gleif.org/en/lei-data/lei-search/search#!body=search&search={lei}",
            },
        )

    def upsert(self, db: Session, record: NormalisedRecord) -> tuple[str, bool]:
        org_id, created = resolve_organisation(db, record.natural_key, record.fields)
        source = get_or_create_source(
            db,
            source_registry_id=None,
            publisher=record.source_meta.get("publisher", "GLEIF"),
            title=record.source_meta.get("title", ""),
            url=record.source_meta.get("url", ""),
            content_hash=record.natural_key.get("lei"),
        )
        record_evidence(
            db,
            subject_type="organisation",
            subject_id=org_id,
            predicate="SOURCE_SUPPORTS_CLAIM",
            object_literal=record.fields.get("legal_name"),
            confidence=95,  # Tier 1 + deterministic LEI match
            verification_state="verified",
            source=source,
            excerpt=f"LEI {record.natural_key.get('lei')} registered legal name.",
            extraction_method="deterministic_id_match",
        )
        return org_id, created
