from app.models.organisation import Organisation
from app.models.resolution import ReviewQueueItem
from app.resolution.confidence import score_claim
from app.resolution.resolver import normalise_name, resolve_organisation


def test_normalise_name_strips_legal_suffixes_and_punctuation():
    assert normalise_name("Terna S.p.A.") == "terna"
    assert normalise_name("Port of Rotterdam N.V.") == "port of rotterdam"


def test_deterministic_lei_match_merges_not_duplicates(db):
    id1, created1 = resolve_organisation(db, {"lei": "AAAAAAAAAAAAAAAAAAAA"}, {"legal_name": "Acme Grid"})
    assert created1 is True
    id2, created2 = resolve_organisation(
        db, {"lei": "AAAAAAAAAAAAAAAAAAAA"}, {"legal_name": "Acme Grid Operator"}
    )
    assert created2 is False
    assert id1 == id2
    assert db.query(Organisation).filter(Organisation.lei == "AAAAAAAAAAAAAAAAAAAA").count() == 1


def test_high_confidence_fuzzy_match_merges(db):
    id1, _ = resolve_organisation(db, {}, {"legal_name": "Autorita di Sistema Portuale del Mar Ligure", "hq_country": "IT"})
    id2, created2 = resolve_organisation(
        db, {}, {"legal_name": "Autorita di Sistema Portuale del Mar Ligure ", "hq_country": "IT"}
    )
    assert created2 is False
    assert id1 == id2


def test_ambiguous_fuzzy_match_creates_new_and_queues_review(db):
    resolve_organisation(db, {}, {"legal_name": "Rotterdam Port", "hq_country": "NL"})
    id2, created2 = resolve_organisation(db, {}, {"legal_name": "Rotterdam Port Group", "hq_country": "NL"})
    assert created2 is True  # never silently merged, never dropped
    queued = db.query(ReviewQueueItem).filter(ReviewQueueItem.entity_type == "organisation").all()
    assert len(queued) == 1
    assert queued[0].status == "pending"


def test_unrelated_names_do_not_match_or_queue(db):
    resolve_organisation(db, {}, {"legal_name": "Deutsche Bahn AG", "hq_country": "DE"})
    id2, created2 = resolve_organisation(db, {}, {"legal_name": "Compagnie des Alpes", "hq_country": "FR"})
    assert created2 is True
    queued = db.query(ReviewQueueItem).all()
    assert len(queued) == 0


def test_confidence_scoring_is_rule_based_not_arbitrary():
    tier1_id_match = score_claim(tier=1, deterministic_id_match=True)
    tier5_no_corroboration = score_claim(tier=5)
    assert tier1_id_match > tier5_no_corroboration
    assert tier1_id_match == 85  # 70 base + 15 deterministic match

    contradicted = score_claim(tier=1, contradicted_by_higher_tier=True)
    assert contradicted == 50  # 70 - 20

    corroborated = score_claim(tier=2, independent_corroborations=3)
    assert corroborated == 75  # 55 base + min(30,20)
