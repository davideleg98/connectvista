"""TED (Tenders Electronic Daily) Search API v3 adapter — EU public
procurement notices. Tier 1, licence: cleared (EU public-sector information,
reuse under the EU Open Data Directive). See lares/SOURCES.md.

Real endpoint (documented, used by fetch() when egress is available):
  POST https://api.ted.europa.eu/v3/notices/search
  body: {"query": "<expert query syntax>", "fields": [...], "page": 1, "limit": 50}

Blocked in this sandbox (ted.europa.eu not in the egress allowlist) — see
ARCHITECTURE.md. Offline fixture at
tests/fixtures/ted/security_cpv_search.json.

CPV codes used for physical-security/resilience relevance (spec §18):
  35120000 surveillance/security systems, 79713000 guard services,
  35125300 detection equipment, 34711000 drones, 42961100 access control,
  79417000 safety/risk/security consultancy.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

import httpx
from sqlalchemy.orm import Session

from app.adapters.base import EgressBlockedError, NormalisedRecord, SourceAdapter
from app.models.events import ProcurementNotice
from app.resolution.provenance import get_or_create_source, record_evidence
from app.resolution.resolver import resolve_organisation

TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

SECURITY_CPV_CODES = [
    "35120000",  # security and surveillance systems
    "79713000",  # guard services
    "35125300",  # detection equipment
    "34711000",  # unmanned aircraft (drones)
    "42961100",  # access control system
    "79417000",  # safety, risk and security consultancy
]

FIELDS = [
    "publication-number",
    "notice-title",
    "buyer-name",
    "buyer-country",
    "publication-date",
    "deadline-receipt-tender-date-lot",
    "classification-cpv",
    "notice-value",
    "winner-name",
]


class TedAdapter(SourceAdapter):
    name = "ted"

    def discover(self, cpv_codes: list[str] | None = None, since: date | None = None) -> Iterable[dict]:
        codes = cpv_codes or SECURITY_CPV_CODES
        since = since or date.today()
        for code in codes:
            query = f'classification-cpv="{code}" AND publication-date>={since:%Y%m%d}'
            yield {"query": query, "cpv": code}

    def fetch(self, item: dict) -> dict:
        body = {"query": item["query"], "fields": FIELDS, "page": 1, "limit": 50}
        try:
            resp = httpx.post(TED_SEARCH_URL, json=body, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise EgressBlockedError(f"ted fetch failed for query {item['query']!r}: {e}") from e

    def parse(self, raw: dict) -> Iterable[dict]:
        yield from raw.get("notices", [])

    def normalise(self, parsed: dict) -> NormalisedRecord:
        buyer_names = parsed.get("buyer-name") or []
        buyer_name = buyer_names[0] if buyer_names else None
        countries = parsed.get("buyer-country") or []
        notice_id = parsed.get("publication-number")
        return NormalisedRecord(
            entity_type="procurement_notice",
            natural_key={"ted_notice_id": notice_id},
            fields={
                "title": (parsed.get("notice-title") or {}).get("eng") or notice_id,
                "buyer_name": buyer_name,
                "country": countries[0] if countries else None,
                "cpv_codes": parsed.get("classification-cpv") or [],
                "published_at": _parse_date(parsed.get("publication-date")),
                "deadline_at": _parse_date(parsed.get("deadline-receipt-tender-date-lot")),
                "value_eur_estimate": (parsed.get("notice-value") or {}).get("amount"),
                "awarded_to_name": (parsed.get("winner-name") or [None])[0],
            },
            source_meta={
                "publisher": "TED - Tenders Electronic Daily",
                "title": (parsed.get("notice-title") or {}).get("eng") or notice_id,
                "url": f"https://ted.europa.eu/en/notice/-/detail/{notice_id}",
                "published_at": _parse_date(parsed.get("publication-date")),
            },
        )

    def upsert(self, db: Session, record: NormalisedRecord) -> tuple[str, bool]:
        notice_id = record.natural_key.get("ted_notice_id")
        existing = db.query(ProcurementNotice).filter(ProcurementNotice.ted_notice_id == notice_id).first()

        contracting_authority_id = None
        if record.fields.get("buyer_name"):
            contracting_authority_id, _ = resolve_organisation(
                db,
                {},
                {"legal_name": record.fields["buyer_name"], "hq_country": record.fields.get("country")},
            )

        security_category = _classify_security_relevance(record.fields.get("cpv_codes", []))

        if existing:
            existing.title = record.fields["title"]
            existing.contracting_authority_org_id = contracting_authority_id
            existing.cpv_codes = record.fields.get("cpv_codes")
            existing.security_relevance_category = security_category
            created = False
            notice = existing
        else:
            notice = ProcurementNotice(
                ted_notice_id=notice_id,
                title=record.fields["title"],
                contracting_authority_org_id=contracting_authority_id,
                cpv_codes=record.fields.get("cpv_codes"),
                security_relevance_category=security_category,
                country=record.fields.get("country"),
                value_eur_estimate=record.fields.get("value_eur_estimate"),
                published_at=record.fields.get("published_at"),
                deadline_at=record.fields.get("deadline_at"),
            )
            db.add(notice)
            db.flush()
            created = True

        source = get_or_create_source(
            db,
            source_registry_id=None,
            publisher=record.source_meta.get("publisher", "TED"),
            title=record.source_meta.get("title", ""),
            url=record.source_meta.get("url", ""),
            published_at=record.source_meta.get("published_at"),
            content_hash=notice_id,
        )
        notice.source_id = source.id
        record_evidence(
            db,
            subject_type="procurement_notice",
            subject_id=notice.id,
            predicate="SOURCE_SUPPORTS_CLAIM",
            object_literal=record.fields["title"],
            confidence=90,
            verification_state="verified",
            source=source,
            excerpt=f"TED notice {notice_id}, CPV {record.fields.get('cpv_codes')}",
            extraction_method="deterministic_id_match",
        )
        return str(notice.id), created


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except ValueError:
        return None


def _classify_security_relevance(cpv_codes: list[str]) -> str | None:
    mapping = {
        "35120000": "surveillance_security_systems",
        "79713000": "guard_services",
        "35125300": "detection_equipment",
        "34711000": "drones_unmanned_systems",
        "42961100": "access_control",
        "79417000": "security_consultancy",
    }
    for code in cpv_codes or []:
        prefix = str(code)[:8]
        if prefix in mapping:
            return mapping[prefix]
    return None
