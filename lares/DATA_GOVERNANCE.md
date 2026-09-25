# Lares — Data Governance

## Licence gate (spec §30)

Every `source_registry` row has a `licence_status`:

- `discovery_only` — default for any source not yet reviewed. Can generate
  hypotheses / candidate entities but must not be bulk-copied into published
  fields, and its facts stay `verification_state='unverified'` until a
  human (or a reviewed licence note) upgrades it.
- `attribution_required` — commercial reuse allowed with attribution (e.g.
  OpenStreetMap/ODbL). Adapter must write the required attribution string
  into `source.attribution_text` and the frontend must render it wherever
  that data is shown (map layer credits, per-record footer).
- `cleared` — commercial reuse confirmed (official APIs/open government data
  with a permissive licence, e.g. TED, GLEIF, EU open data, most national
  transparency/procurement portals).
- `restricted` — do not ingest in bulk; adapter is disabled
  (`source_registry.enabled=false`) until licence is clarified.

No adapter is allowed to flip its own `licence_status` — that's a reviewed,
human-set field (`licence_reviewed_by`, `licence_reviewed_at`,
`licence_notes`).

Concretely at launch:
- OpenStreetMap: `attribution_required`. ODbL — attribution rendered on every
  map view using OSM-derived layers; no redistribution of unmodified bulk
  extracts outside the derived database.
- Google Maps: never ingested/scraped (spec §12, hardcoded refusal). Only
  usable, if ever, as an optional client-rendered basemap through an
  officially licensed Google Maps Platform key the operator supplies — not
  as a data source.
- TED / GLEIF / EU open-data / most national procurement & company
  registries: `cleared` (official public-sector information, explicit reuse
  terms), but pinned in `SOURCES.md` per source with the actual clause cited
  when the adapter is written, not assumed.
- LinkedIn: never scraped. Public profile URLs discovered through ordinary
  web discovery (e.g. cited on a corporate team page) may be stored as a
  reference field on `person`, nothing more.
- Any dataset whose reuse terms are ambiguous when first evaluated:
  `discovery_only` until a human reviews it.

## Sensitive Asset Policy (spec §29)

Enforced at the model layer, not just the UI:
`app/models/infrastructure.py::SENSITIVE_FIELD_ALLOWLIST` restricts which
fields may be non-null when `sensitivity_level='RESTRICTED_PUBLIC'`
(official name, broad public location at administrative-centroid precision,
country/region, branch/authority, high-level public function, official
organisation, public procurement info, public institutional contact
channels, public professional roles). Guard schedules, patrol routines,
access credentials, floorplans, blind spots, sensor placement, internal
procedures, personnel movements and similar are not modelled anywhere in the
ontology — there is no field for them, by design, not just by policy.

Geometry precision degrades automatically with sensitivity:
`STANDARD → exact`, `ELEVATED → approximate (rounded ~500m)`,
`RESTRICTED_PUBLIC → administrative_centroid`. Enforced by a DB trigger
(`enforce_sensitivity_geometry`, see migration
`0002_sensitivity_geometry_trigger`) so it can't be bypassed by an API bug.

## Provenance is mandatory, not optional

The API refuses to publish (`status='published'`) an `infrastructure_asset`
that has zero evidenced claims. This is enforced by
`app/enrichment/lifecycle.py::can_publish()` and covered by a test
(`tests/test_lifecycle.py`).

## Contradictions are stored, not silently overwritten

See `ONTOLOGY.md`'s claim model. `relationship` rows are the *current best*
resolution of possibly many `claim` rows on the same (subject, predicate,
object-slot); superseded claims are kept with `verification_state='disputed'`
if a higher-authority source disagrees, never deleted.
