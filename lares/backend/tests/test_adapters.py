from app.adapters.gleif import GleifAdapter
from app.adapters.overpass import OverpassAdapter
from app.adapters.ted import TedAdapter
from app.models.events import ProcurementNotice
from app.models.infrastructure import InfrastructureAsset
from app.models.organisation import Organisation
from app.models.registry import SourceRegistry
from app.seed.source_registry_seed import seed_source_registry
from tests.conftest import FIXTURES_DIR


def _registry_row(db, name):
    row = db.query(SourceRegistry).filter(SourceRegistry.name == name).first()
    if not row:
        seed_source_registry(db)
        row = db.query(SourceRegistry).filter(SourceRegistry.name == name).first()
    return row


def test_gleif_adapter_offline(db):
    registry = _registry_row(db, "gleif")
    adapter = GleifAdapter()
    result = adapter.run(
        db, registry, offline_fixture=FIXTURES_DIR / "gleif" / "legal_name_search.json"
    )
    assert result.status == "success"
    assert result.records_created == 1
    org = db.query(Organisation).filter(Organisation.lei == "969500PLACEHOLDER001").first()
    assert org is not None
    assert org.legal_name == "Example Grid Operator S.p.A."
    assert org.hq_country == "IT"


def test_gleif_adapter_is_idempotent(db):
    registry = _registry_row(db, "gleif")
    adapter = GleifAdapter()
    fixture = FIXTURES_DIR / "gleif" / "legal_name_search.json"
    adapter.run(db, registry, offline_fixture=fixture)
    result2 = adapter.run(db, registry, offline_fixture=fixture)
    assert result2.records_updated == 1
    assert result2.records_created == 0
    count = db.query(Organisation).filter(Organisation.lei == "969500PLACEHOLDER001").count()
    assert count == 1


def test_ted_adapter_offline(db):
    registry = _registry_row(db, "ted")
    adapter = TedAdapter()
    result = adapter.run(
        db, registry, offline_fixture=FIXTURES_DIR / "ted" / "security_cpv_search.json"
    )
    assert result.status == "success"
    assert result.records_created == 1
    notice = db.query(ProcurementNotice).filter(ProcurementNotice.ted_notice_id == "000000-2026").first()
    assert notice is not None
    assert notice.security_relevance_category == "surveillance_security_systems"
    assert notice.contracting_authority_org_id is not None


def test_overpass_adapter_offline(db):
    registry = _registry_row(db, "overpass")
    adapter = OverpassAdapter()
    result = adapter.run(
        db, registry, offline_fixture=FIXTURES_DIR / "overpass" / "substations_it.json"
    )
    assert result.status == "success"
    assert result.records_created == 1
    asset = db.query(InfrastructureAsset).filter(InfrastructureAsset.osm_id == "way/123456789").first()
    assert asset is not None
    assert asset.category == "energy"
    assert asset.subcategory == "electricity_substation"
    assert asset.geom is not None


def test_adapter_reports_egress_blocked_not_silent_failure(db):
    """The live-fetch path must surface EgressBlockedError distinctly, not
    look like a clean success with zero records (see ARCHITECTURE.md)."""
    registry = _registry_row(db, "gleif")
    adapter = GleifAdapter()
    result = adapter.run(db, registry, discover_kwargs={"legal_names": ["Nonexistent Test Co"]})
    assert result.status in ("failed", "partial")
    assert result.errors
