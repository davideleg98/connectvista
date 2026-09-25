"""Seeds source_registry rows documented in lares/SOURCES.md."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.registry import SourceRegistry

SOURCE_REGISTRY_SEED = [
    dict(
        name="ted",
        tier=1,
        root_domain="ted.europa.eu",
        data_categories=["procurement"],
        geography=["EU", "EEA", "UK"],
        access_method="rest_json",
        update_cadence="daily",
        requires_auth=False,
        licence_status="cleared",
        attribution_required=False,
        licence_notes="EU public procurement data; reuse permitted under the EU Open Data Directive.",
        rate_limit_notes="Documented rate limits apply; adapter batches by CPV code.",
    ),
    dict(
        name="gleif",
        tier=1,
        root_domain="api.gleif.org",
        data_categories=["corporate_ownership"],
        geography=["Global"],
        access_method="rest_json",
        update_cadence="weekly",
        requires_auth=False,
        licence_status="cleared",
        attribution_required=False,
        licence_notes="GLEIF LEI data is published under CC0.",
    ),
    dict(
        name="overpass",
        tier=3,
        root_domain="overpass-api.de",
        data_categories=["geospatial_origination"],
        geography=["Europe"],
        access_method="overpass_ql",
        update_cadence="monthly",
        requires_auth=False,
        licence_status="attribution_required",
        attribution_required=True,
        attribution_text="© OpenStreetMap contributors",
        licence_notes="ODbL. Prefer Geofabrik PBF extracts for bulk import; this adapter is discovery-only.",
    ),
    dict(
        name="entsoe",
        tier=1,
        root_domain="transparency.entsoe.eu",
        data_categories=["energy_transmission"],
        geography=["EU", "EEA", "UK", "Balkans", "Ukraine", "Moldova"],
        access_method="rest_xml",
        update_cadence="daily",
        requires_auth=True,
        required_credential_env="ENTSOE_API_TOKEN",
        licence_status="cleared",
        licence_notes="Transparency Platform data is open; requires a free registration token.",
        enabled=False,  # disabled until ENTSOE_API_TOKEN is supplied — see SOURCES.md
    ),
]


def seed_source_registry(db: Session) -> None:
    for row in SOURCE_REGISTRY_SEED:
        existing = db.query(SourceRegistry).filter(SourceRegistry.name == row["name"]).first()
        if existing:
            continue
        db.add(SourceRegistry(**row))
    db.commit()
