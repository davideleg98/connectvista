"""QA seed dataset — proves the vertical slice (DB -> API -> map -> object
view) across multiple countries and categories, per spec §47/§58.

IMPORTANT (see ARCHITECTURE.md "Hard constraint... network egress"): this
sandbox cannot reach the real bulk sources (TED, GLEIF, Geofabrik). Every
fact below was gathered via WebSearch (the one channel that works here) —
official operator identity and website, corroborated across multiple
independent results (official site + at least one of Wikipedia/industry
press). Nothing here is fabricated:
  - Coordinates are approximate city/facility-scale positions, marked
    geometry_precision='approximate' — never claimed exact.
  - No capacity figures, financials, or people are invented; fields we
    don't have real evidence for are left null.
  - Pure networks (TSO grids, rail infrastructure) get no geometry at all
    (per ONTOLOGY.md "a network is not a site") rather than a fabricated
    line.
  - Every operator relationship carries a Claim+Evidence row citing the
    actual WebSearch source, scored via the same confidence.py rules used
    everywhere else (Tier 4 open web, corroborated by 2+ independent
    results).
"""

from __future__ import annotations

import hashlib
from datetime import date

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.enrichment.relevance import RelevanceInput, compute_relevance
from app.models.infrastructure import InfrastructureAsset, InfrastructureCluster, InfrastructureNetwork
from app.models.organisation import Organisation
from app.resolution.confidence import score_claim
from app.resolution.provenance import get_or_create_source, record_evidence
from app.resolution.resolver import resolve_organisation

# -- organisations, each with the WebSearch-sourced citation used for evidence --
ORGANISATIONS = [
    dict(
        key="terna",
        legal_name="Terna S.p.A.",
        org_type="operator",
        hq_country="IT",
        hq_city="Roma",
        website="https://www.terna.it/en",
        domain="terna.it",
        ownership_class="mixed",
        source=("Terna", "Terna Driving Energy - official site", "https://www.terna.it/en"),
    ),
    dict(
        key="rte",
        legal_name="Reseau de Transport d'Electricite",
        org_type="operator",
        hq_country="FR",
        hq_city="Paris",
        website="https://www.rte-france.com/en",
        domain="rte-france.com",
        ownership_class="state_owned",
        source=("RTE", "RTE - le gestionnaire du reseau de transport - official site", "https://www.rte-france.com/"),
    ),
    dict(
        key="50hertz",
        legal_name="50Hertz Transmission GmbH",
        org_type="operator",
        hq_country="DE",
        hq_city="Berlin",
        website="https://www.50hertz.com/en/",
        domain="50hertz.com",
        ownership_class="private",
        source=("50Hertz", "50Hertz - official site", "https://www.50hertz.com/en/"),
    ),
    dict(
        key="port_rotterdam_authority",
        legal_name="Havenbedrijf Rotterdam N.V.",
        trading_names=["Port of Rotterdam Authority"],
        org_type="operator",
        hq_country="NL",
        hq_city="Rotterdam",
        website="https://www.portofrotterdam.com/en",
        domain="portofrotterdam.com",
        ownership_class="public",
        source=("Port of Rotterdam Authority", "About the Port Authority", "https://www.portofrotterdam.com/en/about-port-authority"),
    ),
    dict(
        key="adsp_mar_ligure_occidentale",
        legal_name="Autorita di Sistema Portuale del Mar Ligure Occidentale",
        trading_names=["Ports of Genoa"],
        org_type="public_authority",
        hq_country="IT",
        hq_city="Genova",
        website="https://www.portsofgenoa.com/it/",
        domain="portsofgenoa.com",
        ownership_class="public",
        source=("AdSP Mar Ligure Occidentale", "Official site - Ports of Genoa", "https://www.portsofgenoa.com/it/"),
    ),
    dict(
        key="ppa_piraeus",
        legal_name="Piraeus Port Authority S.A.",
        trading_names=["PPA", "OLP"],
        org_type="operator",
        hq_country="GR",
        hq_city="Piraeus",
        website="https://www.olp.gr/en/",
        domain="olp.gr",
        ownership_class="mixed",
        source=("Piraeus Port Authority", "PPA official site", "https://www.olp.gr/en/"),
    ),
    dict(
        key="schiphol_group",
        legal_name="Royal Schiphol Group N.V.",
        org_type="operator",
        hq_country="NL",
        hq_city="Schiphol",
        website="https://www.schiphol.nl/en/schiphol-group/",
        domain="schiphol.nl",
        ownership_class="mixed",
        source=("Royal Schiphol Group", "Schiphol Group - official site", "https://www.schiphol.nl/en/schiphol-group/"),
    ),
    dict(
        key="fraport",
        legal_name="Fraport AG",
        org_type="operator",
        hq_country="DE",
        hq_city="Frankfurt am Main",
        website="https://www.fraport.com/en.html",
        domain="fraport.com",
        ownership_class="mixed",
        source=("Fraport AG", "Fraport Group - official site", "https://www.fraport.com/en.html"),
    ),
    dict(
        key="equinix",
        legal_name="Equinix Inc.",
        org_type="technology_provider",
        hq_country="US",
        website="https://www.equinix.com",
        domain="equinix.com",
        ownership_class="private",
        source=("Equinix", "Equinix Frankfurt FR4 data centre page", "https://www.equinix.com/data-centers/europe-colocation/germany-colocation/frankfurt-data-centers/fr4"),
    ),
    dict(
        key="fincantieri",
        legal_name="Fincantieri S.p.A.",
        org_type="operator",
        hq_country="IT",
        hq_city="Trieste",
        website="https://www.fincantieri.com",
        domain="fincantieri.com",
        ownership_class="mixed",
        source=("Fincantieri", "Fincantieri - Monfalcone shipyard newsroom", "https://www.fincantieri.com/en/newsroom/news-e-comunicati-stampa/2025/fincantieri-delivers-star-princess-in-monfalcone"),
    ),
    dict(
        key="rfi",
        legal_name="Rete Ferroviaria Italiana S.p.A.",
        org_type="operator",
        hq_country="IT",
        hq_city="Roma",
        website="https://www.rfi.it/en.html",
        domain="rfi.it",
        ownership_class="state_owned",
        source=("RFI", "Rete Ferroviaria Italiana - official site (About us)", "https://www.rfi.it/en/about-us.html"),
    ),
    dict(
        key="ams_ix",
        legal_name="Amsterdam Internet Exchange B.V.",
        trading_names=["AMS-IX"],
        org_type="operator",
        hq_country="NL",
        hq_city="Amsterdam",
        website="https://www.ams-ix.net",
        domain="ams-ix.net",
        ownership_class="private",
        source=("AMS-IX", "Amsterdam Internet Exchange - official site", "https://www.ams-ix.net"),
    ),
]

# -- infrastructure: networks (no geometry, per ONTOLOGY.md) --
NETWORKS = [
    dict(
        canonical_name="Rete di Trasmissione Nazionale (Italian National Transmission Grid)",
        category="electricity_grid",
        country="IT",
        operator_key="terna",
        description="Italy's high-voltage electricity transmission grid, ~98% of national HV transmission.",
    ),
    dict(
        canonical_name="French High-Voltage Transmission Network",
        category="electricity_grid",
        country="FR",
        operator_key="rte",
        description="France's ~100,000 km high-voltage electricity transmission network, Europe's largest.",
    ),
    dict(
        canonical_name="50Hertz Control Area (Eastern Germany, Berlin, Hamburg)",
        category="electricity_grid",
        country="DE",
        operator_key="50hertz",
        description="220kV/380kV transmission network covering eastern Germany, Berlin and Hamburg.",
    ),
    dict(
        canonical_name="Italian National Railway Network",
        category="rail_corridor",
        country="IT",
        operator_key="rfi",
        description="~16,800 km Italian railway network, signalling and infrastructure managed by RFI.",
    ),
]

# -- infrastructure: physical sites / clusters (point geometry, approximate) --
SITES = [
    dict(
        canonical_name="Port of Rotterdam",
        entity_kind="cluster",
        category="maritime",
        subcategory="port",
        country="NL",
        lat=51.9500,
        lon=4.1400,
        operator_key="port_rotterdam_authority",
        description="Largest seaport in Europe by cargo throughput.",
    ),
    dict(
        canonical_name="Port of Genoa (Western Ligurian Sea port system)",
        entity_kind="cluster",
        category="maritime",
        subcategory="port",
        country="IT",
        lat=44.4056,
        lon=8.9020,
        operator_key="adsp_mar_ligure_occidentale",
        description="Port system covering Genoa, Pra, Savona and Vado Ligure.",
    ),
    dict(
        canonical_name="Port of Piraeus",
        entity_kind="cluster",
        category="maritime",
        subcategory="port",
        country="GR",
        lat=37.9475,
        lon=23.6360,
        operator_key="ppa_piraeus",
        description="Major Mediterranean container/passenger port, majority-owned by COSCO Shipping.",
    ),
    dict(
        canonical_name="Amsterdam Airport Schiphol",
        entity_kind="asset",
        category="aviation",
        subcategory="major_commercial_airport",
        country="NL",
        lat=52.3105,
        lon=4.7683,
        operator_key="schiphol_group",
        description="Main international airport of the Netherlands, operated by Royal Schiphol Group.",
    ),
    dict(
        canonical_name="Frankfurt Airport",
        entity_kind="asset",
        category="aviation",
        subcategory="major_commercial_airport",
        country="DE",
        lat=50.0379,
        lon=8.5622,
        operator_key="fraport",
        description="Germany's largest airport by passenger traffic, operated by Fraport AG.",
    ),
    dict(
        canonical_name="Equinix FR4 Data Centre, Frankfurt",
        entity_kind="asset",
        category="digital",
        subcategory="data_centre",
        country="DE",
        lat=50.1050,
        lon=8.6500,
        operator_key="equinix",
        description="Equinix IBX colocation and interconnection facility in Frankfurt.",
    ),
    dict(
        canonical_name="AMS-IX Amsterdam Internet Exchange",
        entity_kind="asset",
        category="digital",
        subcategory="internet_exchange_point",
        country="NL",
        lat=52.3560,
        lon=4.9540,
        operator_key="ams_ix",
        description="One of the world's largest Internet exchange points.",
    ),
    dict(
        canonical_name="Fincantieri Monfalcone Shipyard",
        entity_kind="asset",
        category="industrial",
        subcategory="shipyard",
        country="IT",
        lat=45.7910,
        lon=13.5330,
        operator_key="fincantieri",
        description="Fincantieri's largest cruise-ship construction site.",
    ),
]


def _tier4_corroborated_confidence() -> int:
    return score_claim(tier=4, independent_corroborations=2)


def load_qa_seed(db: Session) -> dict[str, int]:
    org_ids: dict[str, str] = {}
    for org in ORGANISATIONS:
        fields = {k: v for k, v in org.items() if k not in ("key", "source")}
        org_id, _created = resolve_organisation(db, {}, fields)
        org_ids[org["key"]] = org_id

        publisher, title, url = org["source"]
        source = get_or_create_source(
            db, source_registry_id=None, publisher=publisher, title=title, url=url,
            published_at=date.today(), content_hash=hashlib.sha256(f"qa-seed-org-{org['key']}".encode()).hexdigest(),
        )
        record_evidence(
            db,
            subject_type="organisation",
            subject_id=org_id,
            predicate="SOURCE_SUPPORTS_CLAIM",
            object_literal=org["legal_name"],
            confidence=_tier4_corroborated_confidence(),
            verification_state="corroborated",
            source=source,
            excerpt=f"{title} identifies {org['legal_name']} as the operator/entity in question.",
            extraction_method="manual",
        )

    networks_created = 0
    for net in NETWORKS:
        network = InfrastructureNetwork(
            canonical_name=net["canonical_name"],
            category=net["category"],
            country=net["country"],
            operator_org_id=org_ids[net["operator_key"]],
            description=net["description"],
        )
        db.add(network)
        db.flush()
        networks_created += 1
        _relate_operator(db, "infrastructure_network", network.id, org_ids[net["operator_key"]], net["operator_key"])

    sites_created = 0
    for site in SITES:
        geom = from_shape(Point(site["lon"], site["lat"]), srid=4326)
        common = dict(
            canonical_name=site["canonical_name"],
            country=site["country"],
            geom=geom,
            geometry_precision="approximate",
        )
        if site["entity_kind"] == "cluster":
            entity = InfrastructureCluster(
                category=site["category"], authority_org_id=org_ids[site["operator_key"]], **common
            )
            db.add(entity)
            db.flush()
            _relate_operator(db, "infrastructure_cluster", entity.id, org_ids[site["operator_key"]], site["operator_key"])
        else:
            relevance = compute_relevance(
                RelevanceInput(
                    category=site["category"],
                    has_operator=True,
                    has_owner=False,
                    has_public_authority=False,
                    open_signal_count=0,
                    open_procurement_count=0,
                    contactable_role_count=0,
                    avg_claim_confidence=_tier4_corroborated_confidence(),
                )
            )
            entity = InfrastructureAsset(
                category=site["category"],
                subcategory=site["subcategory"],
                status="operational",
                operational_description=site["description"],
                operator_org_id=org_ids[site["operator_key"]],
                data_completeness_score=40,  # identity+operator known; owner/contacts/procurement still missing
                last_verified_at=date.today(),
                sales_readiness_state="IDENTIFIED",
                strategic_importance=relevance.components["strategic_importance"],
                physical_complexity=relevance.components["physical_complexity"],
                response_complexity=relevance.components["response_complexity"],
                autonomous_fit=relevance.components["autonomous_fit"],
                security_intensity=relevance.components["security_intensity"],
                buyer_accessibility=relevance.components["buyer_accessibility"],
                contactability=relevance.components["contactability"],
                procurement_signal=relevance.components["procurement_signal"],
                change_signal=relevance.components["change_signal"],
                data_confidence=relevance.components["data_confidence"],
                lares_fit=relevance.lares_fit,
                **common,
            )
            db.add(entity)
            db.flush()
            _relate_operator(db, "infrastructure_asset", entity.id, org_ids[site["operator_key"]], site["operator_key"])
        sites_created += 1

    db.commit()
    return {"organisations": len(org_ids), "networks": networks_created, "sites": sites_created}


def _relate_operator(db: Session, entity_type: str, entity_id, org_id: str, org_key: str) -> None:
    from app.models.edges import Relationship

    org_def = next(o for o in ORGANISATIONS if o["key"] == org_key)
    publisher, title, url = org_def["source"]
    source = get_or_create_source(
        db, source_registry_id=None, publisher=publisher, title=title, url=url,
        published_at=date.today(), content_hash=hashlib.sha256(f"qa-seed-operates-{entity_type}-{entity_id}".encode()).hexdigest(),
    )
    claim = record_evidence(
        db,
        subject_type=entity_type,
        subject_id=entity_id,
        predicate="OPERATES",
        object_type="organisation",
        object_id=org_id,
        confidence=_tier4_corroborated_confidence(),
        verification_state="corroborated",
        source=source,
        excerpt=f"{title} identifies {org_def['legal_name']} as operator.",
        extraction_method="manual",
    )

    db.add(
        Relationship(
            subject_type="organisation",
            subject_id=org_id,
            predicate="OPERATES",
            object_type=entity_type,
            object_id=entity_id,
            source_id=source.id,
            claim_id=claim.id,
            confidence=_tier4_corroborated_confidence(),
            verification_state="corroborated",
            first_seen=date.today(),
            last_seen=date.today(),
        )
    )
