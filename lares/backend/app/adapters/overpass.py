"""OpenStreetMap discovery adapter via the Overpass API. Tier 3, licence:
attribution_required (ODbL) — see DATA_GOVERNANCE.md. For actual European-
scale bulk ingestion, prefer Geofabrik PBF extracts + osmium over hammering
the public Overpass endpoint (spec §12) — this adapter is the discovery /
reconciliation motion (Motion A, spec §13), not the bulk importer.

Real endpoint (documented, used by fetch() when egress is available):
  POST https://overpass-api.de/api/interpreter  (body=<Overpass QL>)

Blocked in this sandbox (overpass-api.de not in the egress allowlist) — see
ARCHITECTURE.md. Offline fixture at
tests/fixtures/overpass/substations_it.json.
"""

from __future__ import annotations

from typing import Iterable

import httpx
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.adapters.base import EgressBlockedError, NormalisedRecord, SourceAdapter
from app.resolution.provenance import get_or_create_source, record_evidence
from app.resolution.resolver import resolve_infrastructure_asset

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# OSM tag -> (category, subcategory) mapping. Deliberately small and explicit
# (spec §12: "Import only relevant feature classes").
TAG_CATEGORY_MAP = {
    ("power", "substation"): ("energy", "electricity_substation"),
    ("power", "plant"): ("energy", "power_generation"),
    ("harbour", "yes"): ("maritime", "port"),
    ("aeroway", "aerodrome"): ("aviation", "airport"),
    ("telecom", "data_center"): ("digital", "data_centre"),
    ("man_made", "pipeline"): ("energy", "pipeline"),
}


def build_query(country_area: str, tag_filters: list[tuple[str, str]]) -> str:
    clauses = "".join(f'node["{k}"="{v}"](area.a);way["{k}"="{v}"](area.a);' for k, v in tag_filters)
    return f"""
    [out:json][timeout:60];
    area["ISO3166-1"="{country_area}"][admin_level=2]->.a;
    (
      {clauses}
    );
    out center tags;
    """


class OverpassAdapter(SourceAdapter):
    name = "overpass"

    def discover(self, countries: list[str] | None = None) -> Iterable[dict]:
        for country in countries or []:
            for tag_pair in TAG_CATEGORY_MAP:
                yield {
                    "country": country,
                    "query": build_query(country, [tag_pair]),
                    "tag_pair": tag_pair,
                }

    def fetch(self, item: dict) -> dict:
        try:
            resp = httpx.post(OVERPASS_URL, data={"data": item["query"]}, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise EgressBlockedError(f"overpass fetch failed: {e}") from e

    def parse(self, raw: dict) -> Iterable[dict]:
        yield from raw.get("elements", [])

    def normalise(self, parsed: dict) -> NormalisedRecord:
        tags = parsed.get("tags", {})
        category, subcategory = ("other", "unclassified")
        for (k, v), mapped in TAG_CATEGORY_MAP.items():
            if tags.get(k) == v:
                category, subcategory = mapped
                break

        if "center" in parsed:
            lat, lon = parsed["center"]["lat"], parsed["center"]["lon"]
        else:
            lat, lon = parsed.get("lat"), parsed.get("lon")

        osm_id = f"{parsed.get('type')}/{parsed.get('id')}"
        return NormalisedRecord(
            entity_type="infrastructure_asset",
            natural_key={"osm_id": osm_id},
            fields={
                "canonical_name": tags.get("name") or f"Unnamed {subcategory} ({osm_id})",
                "category": category,
                "subcategory": subcategory,
                "country": tags.get("addr:country"),
                "osm_id": osm_id,
                "geom_lat": lat,
                "geom_lon": lon,
            },
            source_meta={
                "publisher": "OpenStreetMap contributors",
                "title": f"OSM {osm_id}",
                "url": f"https://www.openstreetmap.org/{osm_id}",
            },
        )

    def upsert(self, db: Session, record: NormalisedRecord) -> tuple[str, bool]:
        fields = dict(record.fields)
        lat, lon = fields.pop("geom_lat", None), fields.pop("geom_lon", None)
        if lat is not None and lon is not None:
            fields["geom"] = from_shape(Point(lon, lat), srid=4326)

        asset_id, created = resolve_infrastructure_asset(db, record.natural_key, fields)

        source = get_or_create_source(
            db,
            source_registry_id=None,
            publisher=record.source_meta.get("publisher", "OpenStreetMap contributors"),
            title=record.source_meta.get("title", ""),
            url=record.source_meta.get("url", ""),
            content_hash=record.natural_key.get("osm_id"),
        )
        record_evidence(
            db,
            subject_type="infrastructure_asset",
            subject_id=asset_id,
            predicate="SOURCE_SUPPORTS_CLAIM",
            object_literal=fields.get("canonical_name"),
            confidence=40,  # Tier 3 open geospatial, deterministic OSM id match
            verification_state="corroborated",
            source=source,
            excerpt=f"OSM {record.natural_key.get('osm_id')} tags identify this as {fields.get('subcategory')}.",
            extraction_method="deterministic_id_match",
        )
        return asset_id, created
