# Lares — Architecture

Lares is a persistent European strategic-infrastructure intelligence system: a
graph of infrastructure assets, the organisations that own/operate/regulate
them, the people and roles that buy physical security, the procurement and
projects that create timing, and the signals that create urgency — all with
claim-level provenance.

This is built as a **new, separate application** inside the `connectvista`
repository (`lares/`). It does not touch or depend on the existing CRM app
(`src/`, Supabase). The two apps share only the git repository. If Lares
outgrows sharing a repo with the CRM, it can be split out later with `git
subtree split` — nothing here couples it to `connectvista`.

## Why this stack (deviations from the "preferred" stack are recorded here)

| Layer | Choice | Why |
|---|---|---|
| DB | PostgreSQL 16 + PostGIS 3.4, `pg_trgm`, `pgvector` | Single source of truth, per spec §31. Installed locally (`postgresql-16-postgis-3`). No Neo4j — the ontology is relational with explicit typed edge tables; graph traversal is recursive CTEs / application-level BFS over those edges. Revisit only if query patterns actually demand it. |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, httpx, Pydantic v2 | Per spec §31. |
| Frontend | Vite + React + TypeScript + Tailwind + shadcn/ui + MapLibre GL JS | The spec's preferred frontend is Next.js. This repo's existing app is Vite/React/shadcn/Tailwind. Rather than introduce a second, different React framework (Next.js) alongside the CRM's Vite app purely for stack purity, Lares' frontend reuses the same toolchain the repo already runs, as its own independent Vite project (`lares/web`, own `package.json`, own dev server/port). Nothing in the spec's functional requirements (map, directory, object views, graph, search) requires Next.js specifically — SSR/edge-rendering has no bearing on an internal intelligence tool. MapLibre GL JS is used as specified. deck.gl is deferred until a layer actually needs GPU-scale rendering beyond MapLibre's native layers. |
| Jobs/queue | Not yet implemented (see §Deferred) | Scheduled ingestion needs a queue+worker (Redis + arq/RQ). Deferred behind a clean `IngestionRun` model so it can be added without schema change once real network egress is available (see below). |
| Tiles | Server-side bbox queries against PostGIS now; MVT tile endpoint is the documented upgrade path once asset volume requires it | Avoids shipping full GeoJSON dumps to the browser per spec §23/§32. |

## Hard constraint discovered in this environment: network egress

This sandbox's outbound HTTPS is policy-restricted to an allowlist that does
**not** include the actual data sources this system depends on
(`ted.europa.eu`, `api.gleif.org`, `download.geofabrik.de`, `ec.europa.eu`,
general web domains, even `en.wikipedia.org`) — confirmed via
`/root/.ccr/__agentproxy/status`, which shows `connect_rejected` (403) for
these hosts, and via `WebFetch`, which returns `EGRESS_BLOCKED`. Only
`WebSearch` (routed server-side, not through this proxy) works for external
information in this session.

This means **no live bulk ingestion can run inside this sandbox.** This is
recorded, not worked around, per the operating rules for this session. The
system is built so this is a deployment-environment problem, not an
architecture problem:

- Every `SourceAdapter` is written against the real, documented APIs and is
  production-ready. Each has an **offline fixture mode** (a captured/researched
  JSON sample) so its `parse()`/`normalise()` logic has real tests without
  network access.
- The QA seed dataset (`lares/backend/app/seed/qa_seed.py`) is populated from
  facts gathered via `WebSearch` (the one channel that does work here) plus
  well-established public knowledge, entered as claims with explicit
  `verification_state='unverified'` / a named source, never fabricated. It
  exists to prove the vertical slice (DB → API → map → object view), **not**
  as a claim of production coverage.
- When Lares is deployed somewhere with normal internet egress (or this
  session's network policy is widened), the adapters in
  `lares/backend/app/adapters/` are the actual ingestion code — turn on the
  scheduler and they run.

## Data flow

```
SourceAdapter.discover() → .fetch() → raw storage (raw_documents, hashed)
   → .parse() → .normalise() → candidate rows
   → entity resolution (deterministic ID → fuzzy match → review queue)
   → PostGIS upsert (infrastructure_asset / organisation / ...)
   → claim + evidence rows (provenance, never overwritten silently)
   → enrichment pipeline stages (operator → owner → ultimate parent →
     contacts → projects → procurement → news → relevance scoring → QA)
   → API → web app
```

Every relationship and every fact-bearing field is backed by one or more
`claim` rows pointing at `evidence` rows pointing at `source` rows. See
`ONTOLOGY.md`.

## Repository layout

```
lares/
  ARCHITECTURE.md
  ONTOLOGY.md
  SOURCES.md
  SOURCE_BACKLOG.md
  DATA_GOVERNANCE.md
  DEVELOPMENT.md
  CLAUDE.md
  docker-compose.yml
  backend/
    app/
      core/          # config, db session, settings
      models/         # SQLAlchemy ORM = the ontology
      adapters/        # SourceAdapter framework + concrete adapters
      resolution/      # entity resolution pipeline
      enrichment/      # relevance scoring, brief generation
      api/             # FastAPI routers
      seed/            # QA seed dataset loader
    alembic/           # migrations
    tests/
  web/
    src/
      pages/           # Map, Infrastructure directory/detail, Organisation, Search
      components/
      lib/
```

## Deferred (explicitly out of scope for this pass, tracked so it isn't lost)

- Redis/worker scheduler for cadenced ingestion (design is ready: `source` +
  `ingestion_run` tables already model cadence/last_checked/last_changed).
- MVT vector tiles (bbox JSON queries are the interim, already
  bounded/paginated).
- LLM-based extraction/classification (extraction schemas are defined in
  `ONTOLOGY.md`'s claim model so this slots in later without a schema change).
- Country Expansion Agent tooling (§49) — the Source Registry schema supports
  it; the research automation itself is future work.
