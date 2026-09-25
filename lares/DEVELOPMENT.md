# Lares — Development

## Quick start

### Option A — Docker Compose (production-shaped, needs image-pull network access)

```bash
cd lares
docker compose up
```

Brings up Postgres+PostGIS on 5432, the API on 8123, the web app on 5183.
The backend container runs `alembic upgrade head` on start; seed data is not
auto-loaded (run it explicitly, see below) so you control what's in the DB.

### Option B — Local processes (what this was actually developed against)

This sandbox's Docker cannot pull images through the egress policy, so
development happened against a locally-installed Postgres+PostGIS instead.
Both work identically against the same `DATABASE_URL`.

```bash
# 1. Postgres + PostGIS (adjust to your platform's package manager)
sudo apt-get install -y postgresql-16-postgis-3 postgresql-16-pgvector
sudo service postgresql start
sudo -u postgres psql -c "CREATE ROLE lares LOGIN PASSWORD 'lares';"
sudo -u postgres psql -c "CREATE DATABASE lares OWNER lares;"
sudo -u postgres psql -d lares -c "CREATE EXTENSION postgis; CREATE EXTENSION pg_trgm; CREATE EXTENSION pgcrypto; CREATE EXTENSION vector;"

# 2. Backend
cd lares/backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp ../.env.example ../.env   # edit if your DB differs
./.venv/bin/alembic upgrade head
./.venv/bin/python scripts/seed_all.py     # source registry + QA dataset
./.venv/bin/uvicorn app.main:app --port 8123

# 3. Frontend (separate terminal)
cd lares/web
npm install
cp .env.example .env
npm run dev -- --port 5183
```

Open http://localhost:5183 — note **localhost**, not `127.0.0.1`: the
backend's CORS is scoped to `LARES_WEB_ORIGIN` and the two are different
origins to a browser.

## Running tests

```bash
cd lares/backend
./.venv/bin/pytest tests/ -v
```

Tests run against the real dev Postgres inside a transaction that's rolled
back after each test (see `tests/conftest.py`) — no separate test database
needed, and nothing they do persists.

## Ingesting data

Each adapter in `app/adapters/` can run against its offline fixture (for
tests) or live (in an environment whose network policy allows reaching the
actual host — this sandbox's does not, see ARCHITECTURE.md):

```python
from app.core.db import SessionLocal
from app.adapters.ted import TedAdapter
from app.models.registry import SourceRegistry

db = SessionLocal()
registry = db.query(SourceRegistry).filter_by(name="ted").first()
TedAdapter().run(db, registry)  # live; add offline_fixture=Path(...) to replay a fixture
```

Every run writes an `ingestion_run` row — inspect via
`GET /api/sources/ingestion-runs` or the Sources page in the web app.

## Adding a new source adapter

See `lares/SOURCES.md` "Adding a new adapter" — register in
`source_registry_seed.py`, subclass `SourceAdapter`, add an offline fixture
and a test. Do not flip `licence_status` away from `discovery_only` yourself
— that's a reviewed field (see `DATA_GOVERNANCE.md`).

## How entity resolution works

`app/resolution/resolver.py` — deterministic ID match first (LEI, company
number+jurisdiction, OSM id, facility code), then `pg_trgm` name similarity
scoped by country. A high-similarity match merges (fills nulls only, never
overwrites). A mid-band ("ambiguous") match creates a new record *and* logs
a `review_queue_item` — nothing is silently merged or silently dropped. See
`ONTOLOGY.md` "Design rules".

## How scheduling works (current state)

Not yet wired to a scheduler — see ARCHITECTURE.md "Deferred". The
`source_registry.update_cadence` field and `ingestion_run` history already
model what a scheduler needs; adding Redis + a worker (arq/RQ) that calls
`adapter.run()` on cadence is the next step and requires no schema change.

## Inspecting errors

- `GET /api/sources/ingestion-runs` — per-run status, counts, and the
  `errors` list (adapters classify failures as `MissingCredentialError` /
  `EgressBlockedError` / other, so "the source's network is blocked" and
  "the source rejected our request" don't look the same).
- `review_queue_item` table / `GET /api/review-queue` — entity resolution
  matches awaiting human confirmation. Approve (`POST
  /api/review-queue/{id}/approve`) merges the candidate into the matched
  record — re-pointing its claims and relationships, filling any fields the
  survivor is missing, logging a `merge_log` row, then removing the
  now-redundant duplicate. Reject (`.../reject`) confirms they're genuinely
  different and leaves both records untouched. See the Review Queue page in
  the web app.

## Sensitive assets

See `DATA_GOVERNANCE.md` "Sensitive Asset Policy" — enforced by a DB
trigger (`enforce_sensitivity_geometry`, migration `bf8f0f581ce5`), not just
application code.

## Licences

See `DATA_GOVERNANCE.md` "Licence gate" and `SOURCES.md`. New sources start
`discovery_only` until a human reviews and records the actual licence terms.
