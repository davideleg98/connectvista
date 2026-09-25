# CLAUDE.md — lares/

Guidance for future Claude Code sessions working in this directory.

## What this is

A European strategic-infrastructure intelligence system (Palantir-Foundry-
shaped, not a lead-generation table), built as a **separate application**
inside the `connectvista` repository — see `ARCHITECTURE.md` for why, and
for what it deliberately does *not* share with the CRM app in `../src`.

Read `ARCHITECTURE.md` and `ONTOLOGY.md` before making structural changes.
They record real decisions (including the hard network-egress constraint of
the sandbox this was first built in) — don't re-derive them from scratch.

## Ground rules carried over from the founding spec

- **Provenance is mandatory.** Every fact-bearing relationship or claim
  needs a `Source`+`Claim`+`Evidence` row. Don't add a field that gets
  populated without one. See `DATA_GOVERNANCE.md`.
- **Unknown beats invented.** Never fabricate a person, contact, capacity
  figure, or coordinate. Null + low `data_completeness_score` is correct;
  a plausible-looking guess is not. This applies doubly to QA/seed data —
  see the header comment in `app/seed/qa_seed.py` for how existing seed
  data was sourced (WebSearch, corroborated, never invented).
- **Entities over rows.** When extending ingestion, prefer improving entity
  resolution (`app/resolution/resolver.py`) over adding more raw records.
- **Confidence is rule-based**, not an LLM-guessed float — see
  `app/resolution/confidence.py`. Extend the rules; don't bypass them.
- **Sensitivity policy is enforced in the DB**, not just at render time —
  see the `enforce_sensitivity_geometry` trigger. Don't add a field to
  `InfrastructureAsset` that could carry the kind of information listed as
  forbidden in `DATA_GOVERNANCE.md` "Sensitive Asset Policy".
- **Licence status is a reviewed field.** A new adapter starts
  `discovery_only`; don't have the adapter or an LLM upgrade its own
  licence status.

## Commands

See `DEVELOPMENT.md` for the full setup. Fast reference:

```bash
cd lares/backend && ./.venv/bin/pytest tests/ -v       # tests
cd lares/backend && ./.venv/bin/alembic upgrade head    # migrate
cd lares/backend && ./.venv/bin/python scripts/seed_all.py  # seed
cd lares/web && npm run dev -- --port 5183               # frontend
```

## Known gaps (see ARCHITECTURE.md "Deferred" for the full list)

- No scheduler yet (Redis+worker) — adapters run on demand via `.run()`.
- Only 3 source adapters implemented end-to-end (TED, GLEIF, Overpass) plus
  a stubbed/disabled ENTSO-E adapter awaiting a credential. See
  `SOURCE_BACKLOG.md` for what's next, and `SOURCES.md` for what's live.
- QA seed data is 12 organisations / 12 infrastructure objects across 5
  countries and 6 categories — enough to prove the vertical slice end to
  end, not "Europe is covered". See the Coverage page (`/coverage`) and
  `DATA_QUALITY` section of `ARCHITECTURE.md`'s roadmap for what "covered"
  should mean once real ingestion runs.
- No MVT tiles, no LLM extraction pipeline, no Country Expansion Agent
  tooling — all explicitly deferred with a stated reason, not forgotten.

## When you pick this back up

Don't restart from a clean slate. Read the docs above, run the test suite,
seed the DB, run the app, and look at what's actually there before deciding
what to build next. The engineering-judgement rules in the founding spec
still apply: better entities over more rows, provenance over AI narrative,
ontology over dashboard polish, workflow over generic CRUD.
