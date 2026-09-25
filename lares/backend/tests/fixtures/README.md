Fixtures in this directory are **hand-authored, structurally realistic
samples** shaped like each source's real, documented API response schema.
They exist so adapter `parse()`/`normalise()` logic has offline tests in an
environment whose network egress is policy-blocked to these hosts (see
`lares/ARCHITECTURE.md`). They are NOT captured live responses and their
values (LEI codes, notice IDs, OSM ids) are illustrative placeholders, not
verified real-world identifiers — do not treat them as data.
