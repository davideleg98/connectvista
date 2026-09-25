# Lares — Source Registry (implemented adapters)

Each row below corresponds to a `source_registry` record created by
`lares/backend/app/seed/source_registry_seed.py`. "Runnable here" reflects
this sandbox's network egress policy (see ARCHITECTURE.md) — every adapter
is production-code, tested offline against a fixture, and NOT executed live
in this environment.

| Source | Tier | Categories | Geography | Access method | Licence status | Runnable here |
|---|---|---|---|---|---|---|
| TED (Tenders Electronic Daily) Search API v3 | 1 | Procurement | EU/EEA/UK | REST/JSON, `api.ted.europa.eu/v3/notices/search` | cleared (EU public procurement data, reuse per EU Open Data Directive) | No (egress blocked to `ted.europa.eu`) |
| GLEIF API v1 | 1/2 | Corporate ownership (LEI + Level 2 parent relationships) | Global, filter EU | REST/JSON, `api.gleif.org/api/v1/...` | cleared (GLEIF data is open, CC0) | No (egress blocked to `api.gleif.org`) |
| OpenStreetMap (Overpass API for discovery; Geofabrik PBF extracts preferred for bulk) | 3 | Geospatial origination for all categories | Europe-wide | Overpass QL / PBF extract + osmium | attribution_required (ODbL) | No (egress blocked to `overpass-api.de` / `download.geofabrik.de`) |
| European Commission TEN-T / TENtec | 1 | Ports, airports, rail freight terminals, corridors | EU-27 (+ neighbourhood) | Dataset download / WFS | cleared (EU open data) — verify specific dataset licence at integration time | No (egress blocked to `ec.europa.eu` / `transport.ec.europa.eu`) |
| ENTSO-E Transparency Platform | 1 | Electricity transmission, generation | EU/EEA/UK/Balkans/Ukraine/Moldova (ENTSO-E membership) | REST/XML, API-token gated | cleared for the transparency data itself; token required (missing credential, see below) | No — also needs a credential the user must supply |

## Missing credentials (recorded, not blocking)

- `ENTSOE_API_TOKEN` — required for ENTSO-E Transparency Platform. Free
  self-service registration at their platform; not obtainable from inside
  this sandbox (no email/registration flow reachable). Adapter
  (`app/adapters/entsoe.py`) reads it from `ENTSOE_API_TOKEN` and raises a
  clear `MissingCredentialError` if absent, rather than failing silently.
- `GOOGLE_MAPS_API_KEY` (optional, basemap only, never a data source) — see
  DATA_GOVERNANCE.md.

## Adding a new adapter

1. Add a `source_registry` row (see `app/seed/source_registry_seed.py`) with
   tier, categories, geography, access method, and `licence_status` starting
   at `discovery_only` unless the licence is already confirmed.
2. Implement `app/adapters/<name>.py` subclassing `SourceAdapter`
   (`discover/fetch/parse/normalise/validate/upsert`), with a fixture file
   under `tests/fixtures/<name>/` and a test that runs `parse`+`normalise`
   against it without network access.
3. Wire cadence in `source_registry.cadence` (see ARCHITECTURE.md's update
   cadence table) — the scheduler (deferred, see ARCHITECTURE.md) will pick
   it up once implemented.

See `SOURCE_BACKLOG.md` for the country × sector backlog of sources not yet
implemented.
