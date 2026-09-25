# Lares — Ontology

The core model is a graph, not a table of leads. Object types are nouns;
relationships are first-class, typed, timestamped and evidenced.

## Design rules

1. **A network is not a site.** A submarine cable, a transmission grid, a gas
   pipeline are `InfrastructureNetwork`. A landing station, a substation, a
   compressor station are `PhysicalSite` (or the `Asset` at that site). Ports
   are `InfrastructureCluster`s containing multiple `PhysicalSite`s
   (terminals) each potentially with a different operator.
2. **Every fact-bearing field or relationship is a claim**, not a raw column
   value. `infrastructure_asset.canonical_name` is allowed to be a plain
   column because identity has to exist before it can be claimed about — but
   `operated_by`, `owned_by`, capacity figures, etc. are **edges** or
   **claims**, each with a `source_id`, `confidence`, `first_seen`,
   `last_seen`, `verification_state`.
3. **Unknown beats invented.** A null operator with `data_completeness`
   reflecting that is correct. A guessed operator is not.
4. **Merges never delete history.** Entity resolution merges write a
   `merge_log` row and keep the losing record's claims re-pointed at the
   surviving entity, not deleted.

## Object types

### Core entities

- **InfrastructureAsset** — the physical thing (a substation, a terminal, a
  data centre, a plant). Fields: id, canonical_name, alt_names[],
  category, subcategory, status, country (ISO-3166-1 alpha-2), nuts_region,
  municipality, geom (PostGIS Point/Polygon), geometry_precision
  (`exact`|`approximate`|`administrative_centroid`|`withheld`),
  sensitivity_level (`STANDARD`|`ELEVATED`|`RESTRICTED_PUBLIC`),
  data_completeness_score, last_verified_at, last_updated_at.
- **PhysicalSite** — a location that can host one or more assets/operators
  (used when an `InfrastructureCluster` like a port needs distinct terminals
  with distinct operators). Same geometry/sensitivity fields as above.
- **InfrastructureNetwork** — a network-scale asset (grid, pipeline, cable
  system, rail corridor). geom is LineString/MultiLineString or null when
  only membership is known.
- **InfrastructureCluster** — groups sites that are operationally one entity
  to the outside world but administratively distinct inside (a port, an
  airport system).
- **Organisation** — any legal/operating entity: operator, owner, ultimate
  parent, security provider, technology provider, vendor. Type is a field
  (`operator|owner|parent|authority|security_provider|technology_provider|
  supplier|other`), not a separate table, because the same organisation can
  hold multiple roles across different assets.
- **PublicAuthority** — government/regulatory/municipal bodies. Modelled as
  a specialised `Organisation` row (`org_type='public_authority'`) plus a
  `public_authority_detail` table for jurisdiction-specific fields.
- **Person** — public professional identity only (name, public role,
  organisation, public profile URL, source). Never inferred contact info.
- **Role** — an organisational buying function, independent of whether a
  named person currently holds it (`CSO`, `Head of Physical Security`,
  `Port Security`, `HSSE`, `Procurement`, `Innovation/Autonomous Systems`,
  ...). `role_category` enum + free-text `title` as seen in the source.
- **Project** — CAPEX / expansion / greenfield / EU-funded programme.
- **ProcurementNotice** — a TED (or national) tender.
- **Contract** — an awarded outcome of a `ProcurementNotice` (or a
  privately-sourced contract signal).
- **Event / Signal** — a "why now" fact with a type, date, decay/expiry, and
  commercial relevance note.
- **Source** — one row per origin *document/dataset instance*, not per
  domain — see Source Registry vs. Source below.
- **SourceRegistry** — one row per *adapter* (config, licence terms, cadence,
  reliability) — the thing SOURCES.md documents.
- **Claim / Evidence** — see below.
- **Watchlist / WatchlistItem** — user-curated follow lists.
- **Interaction** — a recorded outreach action (Mark Contacted, Add Note...).

### Relationship (edge) types

Stored in a single polymorphic `relationship` table
(`subject_type, subject_id, predicate, object_type, object_id`) rather than
one table per predicate, so graph traversal is one query shape. Predicates
(the spec's list in full):

`OWNS, OPERATES, CONTROLS, ULTIMATELY_OWNED_BY, PART_OF, LOCATED_AT,
LOCATED_IN, CONNECTS_TO, REGULATED_BY, AUTHORISED_BY, MANAGED_BY,
PROCURES_FROM, CONTRACTED_WITH, ANNOUNCED_PROJECT, INVESTING_IN, HAS_ROLE,
WORKS_AT, MENTIONED_IN, AFFECTED_BY_EVENT, PARTICIPATES_IN_PROJECT,
ISSUED_TENDER, WON_TENDER, RELATED_TO, SOURCE_SUPPORTS_CLAIM`

Every relationship row carries: `source_id` (→ `source`), `confidence`
(0-100, rule-derived — see below), `first_seen`, `last_seen`,
`valid_from`/`valid_to` (nullable), `verification_state`
(`unverified|corroborated|verified|disputed`).

### Claim / Evidence model

For any fact worth showing with "why do we believe this":

```
claim(id, subject_type, subject_id, predicate, object_type, object_id,
      object_literal,            -- for scalar claims (e.g. a capacity figure)
      confidence, verification_state, created_at)

evidence(id, claim_id, source_id, publisher, title, url, published_at,
         retrieved_at, excerpt, extraction_method
         ('manual'|'regex'|'llm_extraction'|'deterministic_id_match'))
```

A `relationship` row and a `claim` row are deliberately similar; a
relationship is the resolved, published version, a claim is the raw,
possibly-contradicting input. Contradicting claims about the same
(subject, predicate, object-slot) are **both kept**; the relationship layer
picks the current best one by confidence/source-authority and the UI can
show "1 conflicting source" (spec §39).

### Confidence model (deterministic, not an LLM-guessed float)

Base points by source tier (see SOURCES.md): Tier 1 = 70, Tier 2 = 55,
Tier 3 = 40, Tier 4 = 25, Tier 5 = 10. Adjustments: +15 deterministic ID
match (LEI/company number/OSM id equal), +10 per additional independent
corroborating source (capped +20), -20 if a Tier 1/2 source contradicts it,
recency decay -1/month past 18 months for volatile predicates
(`HAS_ROLE`, `PROCURES_FROM`). Clamped to [0,100]. Implemented in
`app/resolution/confidence.py` as explicit rules, not a model call.

## Lares relevance model

Ten explicit component scores (0-100 each), stored individually — never
collapsed into an unexplained single number without the breakdown attached:
`strategic_importance, physical_complexity, response_complexity,
autonomous_fit, security_intensity, buyer_accessibility, contactability,
procurement_signal, change_signal, data_confidence`. `lares_fit` is a
documented weighted function of the above (`app/enrichment/relevance.py`),
with the weights and the per-component rationale returned by the API, not
hidden.

## Sales-readiness lifecycle

`DISCOVERED → NEEDS_ENRICHMENT → IDENTIFIED → QUALIFIED → OUTREACH_READY`,
with side-states `WATCH`, `DISQUALIFIED`. Transition rules live in
`app/enrichment/lifecycle.py` and are re-evaluated on every enrichment run,
not set once by hand.

## Sensitivity policy

`sensitivity_level ∈ {STANDARD, ELEVATED, RESTRICTED_PUBLIC}`. Defence /
military assets default to `RESTRICTED_PUBLIC`: geometry is truncated to
`administrative_centroid` precision, and only the field allowlist in
§29 of the founding spec (official name, broad location, country/region,
branch/authority, high-level public function, official org, public
procurement info, public institutional contact channels, public roles) is
populated — enforced in `app/models/infrastructure.py` via a
`SENSITIVE_FIELD_ALLOWLIST` check at write time, not just at render time.
