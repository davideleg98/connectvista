from datetime import date

from fastapi.testclient import TestClient
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.api.deps import get_db
from app.main import app
from app.models.infrastructure import InfrastructureAsset
from app.models.organisation import Organisation
from app.resolution.provenance import get_or_create_source, record_evidence


def _client(db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _seed_one_asset(db):
    org = Organisation(legal_name="Test Port Authority", org_type="operator", hq_country="IT")
    db.add(org)
    db.flush()

    asset = InfrastructureAsset(
        canonical_name="Test Port Terminal",
        category="maritime",
        subcategory="port",
        country="IT",
        status="operational",
        operator_org_id=org.id,
        geom=from_shape(Point(9.0, 45.0), srid=4326),
        geometry_precision="approximate",
        lares_fit=42,
    )
    db.add(asset)
    db.flush()

    source = get_or_create_source(
        db, source_registry_id=None, publisher="Test Publisher", title="Test Title",
        url="https://example.com/test", published_at=date.today(), content_hash="testhash123",
    )
    record_evidence(
        db, subject_type="infrastructure_asset", subject_id=asset.id, predicate="OPERATES",
        object_type="organisation", object_id=org.id, confidence=50, verification_state="corroborated",
        source=source, excerpt="test excerpt",
    )
    db.commit()
    return asset, org


def test_health():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_and_filter_infrastructures(db):
    asset, _org = _seed_one_asset(db)
    client = _client(db)

    resp = client.get("/api/infrastructures", params={"country": "IT", "category": "maritime"})
    assert resp.status_code == 200
    body = resp.json()
    assert any(item["id"] == str(asset.id) for item in body["items"])

    resp_wrong_country = client.get("/api/infrastructures", params={"country": "DE", "category": "maritime"})
    assert not any(item["id"] == str(asset.id) for item in resp_wrong_country.json()["items"])


def test_infrastructure_detail_has_evidence_and_org_graph(db):
    asset, org = _seed_one_asset(db)
    client = _client(db)

    resp = client.get(f"/api/infrastructures/{asset.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["canonical_name"] == "Test Port Terminal"
    assert body["organisation_graph"][0]["legal_name"] == "Test Port Authority"
    assert len(body["evidence"]) >= 1
    assert body["evidence"][0]["source_url"] == "https://example.com/test"


def test_infrastructure_detail_404(db):
    client = _client(db)
    resp = client.get("/api/infrastructures/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_organisation_portfolio_lists_operated_infrastructure(db):
    asset, org = _seed_one_asset(db)
    client = _client(db)

    resp = client.get(f"/api/organisations/{org.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert any(p["id"] == str(asset.id) for p in body["infrastructure_portfolio"])


def test_map_bbox_filters_by_extent(db):
    asset, _org = _seed_one_asset(db)
    client = _client(db)

    inside = client.get("/api/map/bbox", params={"min_lon": 8, "min_lat": 44, "max_lon": 10, "max_lat": 46})
    assert any(f["id"] == str(asset.id) for f in inside.json()["features"])

    outside = client.get("/api/map/bbox", params={"min_lon": 100, "min_lat": 60, "max_lon": 110, "max_lat": 65})
    assert not any(f["id"] == str(asset.id) for f in outside.json()["features"])


def test_search_finds_infrastructure_and_organisation(db):
    asset, org = _seed_one_asset(db)
    client = _client(db)

    resp = client.get("/api/search", params={"q": "Test Port"})
    body = resp.json()
    assert any(i["id"] == str(asset.id) for i in body["infrastructures"])
    assert any(o["id"] == str(org.id) for o in body["organisations"])


def test_coverage_matrix_counts_by_country_and_category(db):
    _seed_one_asset(db)
    client = _client(db)

    resp = client.get("/api/coverage")
    matrix = resp.json()["matrix"]
    assert matrix["IT"]["maritime"]["candidates"] >= 1
    assert matrix["IT"]["maritime"]["with_operator"] >= 1


def test_review_queue_approve_merges_and_repoints_evidence(db):
    from app.resolution.resolver import resolve_organisation

    survivor_id, _ = resolve_organisation(db, {}, {"legal_name": "Rotterdam Port", "hq_country": "NL"})
    candidate_id, created = resolve_organisation(
        db, {}, {"legal_name": "Rotterdam Port Group", "hq_country": "NL", "website": "https://example.com"}
    )
    assert created is True

    source = get_or_create_source(
        db, source_registry_id=None, publisher="Test", title="Test", url="https://example.com/x",
        published_at=date.today(), content_hash="review-queue-test-hash",
    )
    record_evidence(
        db, subject_type="organisation", subject_id=candidate_id, predicate="SOURCE_SUPPORTS_CLAIM",
        object_literal="Rotterdam Port Group", confidence=40, verification_state="unverified",
        source=source, excerpt="test excerpt",
    )
    db.commit()

    client = _client(db)
    item_id = client.get("/api/review-queue").json()["items"][0]["id"]

    resp = client.post(f"/api/review-queue/{item_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["surviving_id"] == survivor_id

    # candidate row is gone, survivor picked up the field it was missing
    assert db.get(Organisation, candidate_id) is None
    survivor = db.get(Organisation, survivor_id)
    assert survivor.website == "https://example.com"

    # the claim that pointed at the candidate now points at the survivor —
    # evidence is never destroyed by a merge
    from app.models.provenance import Claim

    repointed = db.query(Claim).filter(
        Claim.subject_type == "organisation", Claim.subject_id == survivor.id
    ).all()
    assert any(c.object_literal == "Rotterdam Port Group" for c in repointed)

    assert client.get("/api/review-queue").json()["items"] == []


def test_review_queue_reject_keeps_both_records(db):
    from app.resolution.resolver import resolve_organisation

    resolve_organisation(db, {}, {"legal_name": "Rotterdam Port", "hq_country": "NL"})
    candidate_id, created = resolve_organisation(
        db, {}, {"legal_name": "Rotterdam Port Group", "hq_country": "NL"}
    )
    assert created is True
    db.commit()

    client = _client(db)
    item_id = client.get("/api/review-queue").json()["items"][0]["id"]

    resp = client.post(f"/api/review-queue/{item_id}/reject")
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

    # both organisations still exist, untouched
    assert db.get(Organisation, candidate_id) is not None
    assert client.get("/api/review-queue").json()["items"] == []
    assert client.get("/api/review-queue", params={"status": "rejected"}).json()["items"][0]["id"] == item_id
