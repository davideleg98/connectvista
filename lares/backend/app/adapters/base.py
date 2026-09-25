"""SourceAdapter framework. See lares/ARCHITECTURE.md §Data flow and
lares/SOURCES.md.

Every adapter separates discover -> fetch -> parse -> normalise -> validate
-> upsert (spec §33) so raw, normalised and resolved data stay distinct and
each stage is independently rerunnable. `run()` is the orchestrator that
also writes an `IngestionRun` row (spec §54 observability) and is
incremental: `fetch()` results are hashed and unchanged content is skipped.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy.orm import Session

from app.models.registry import IngestionRun, SourceRegistry


class MissingCredentialError(RuntimeError):
    """Raised when an adapter needs a credential that isn't configured.

    Per the operating rules for this project: never fail silently and never
    stop the project. The caller records this against the SourceRegistry row
    and moves on. See lares/SOURCES.md "Missing credentials".
    """


class EgressBlockedError(RuntimeError):
    """Raised when live fetch is attempted in an environment whose network
    policy does not allow it (this sandbox). Adapters distinguish this from
    a real fetch failure so ingestion runs report the true cause.
    """


@dataclass
class NormalisedRecord:
    entity_type: str  # infrastructure_asset|organisation|procurement_notice|relationship|...
    natural_key: dict[str, Any]  # deterministic fields used by entity resolution (LEI, osm_id, ted_notice_id...)
    fields: dict[str, Any]
    source_meta: dict[str, Any] = field(default_factory=dict)  # publisher, title, url, published_at, excerpt


@dataclass
class IngestionRunResult:
    status: str
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_rejected: int = 0
    errors: list[str] = field(default_factory=list)


class SourceAdapter(ABC):
    name: str

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path(__file__).resolve().parents[2] / "data" / "raw" / self.name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- pipeline stages -----------------------------------------------
    @abstractmethod
    def discover(self, **kwargs) -> Iterable[dict]:
        """Enumerate candidate fetch targets (e.g. search queries, id lists)."""

    @abstractmethod
    def fetch(self, item: dict) -> dict:
        """Retrieve one raw payload. Must raise EgressBlockedError/
        MissingCredentialError rather than returning empty/fake data."""

    @abstractmethod
    def parse(self, raw: dict) -> Iterable[dict]:
        """Raw payload -> list of loosely-structured records."""

    @abstractmethod
    def normalise(self, parsed: dict) -> NormalisedRecord:
        """Parsed record -> NormalisedRecord ready for entity resolution."""

    def validate(self, record: NormalisedRecord) -> bool:
        return bool(record.natural_key) and bool(record.fields)

    @abstractmethod
    def upsert(self, db: Session, record: NormalisedRecord) -> tuple[str, bool]:
        """Persist via entity resolution. Returns (entity_id, created)."""

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def content_hash(raw: dict) -> str:
        blob = json.dumps(raw, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def cache_raw(self, key: str, raw: dict) -> Path:
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps(raw, indent=2, default=str))
        return path

    def load_fixture(self, fixture_path: Path) -> dict:
        return json.loads(fixture_path.read_text())

    # -- orchestration -----------------------------------------------------
    def run(
        self,
        db: Session,
        source_registry: SourceRegistry,
        *,
        offline_fixture: Path | None = None,
        discover_kwargs: dict | None = None,
    ) -> IngestionRunResult:
        run_row = IngestionRun(
            source_registry_id=source_registry.id,
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        db.add(run_row)
        db.flush()

        result = IngestionRunResult(status="running")
        try:
            items = (
                [{"offline_fixture": offline_fixture}]
                if offline_fixture is not None
                else list(self.discover(**(discover_kwargs or {})))
            )
            for item in items:
                try:
                    raw = (
                        self.load_fixture(item["offline_fixture"])
                        if item.get("offline_fixture")
                        else self.fetch(item)
                    )
                    result.records_fetched += 1
                    for parsed in self.parse(raw):
                        record = self.normalise(parsed)
                        if not self.validate(record):
                            result.records_rejected += 1
                            continue
                        _id, created = self.upsert(db, record)
                        if created:
                            result.records_created += 1
                        else:
                            result.records_updated += 1
                except (MissingCredentialError, EgressBlockedError) as e:
                    result.errors.append(str(e))
                except Exception as e:  # isolate failure of one item, per spec §33
                    result.errors.append(f"{type(e).__name__}: {e}")
                    result.records_rejected += 1

            result.status = "success" if not result.errors else "partial"
        except (MissingCredentialError, EgressBlockedError) as e:
            result.status = "failed"
            result.errors.append(str(e))
        finally:
            run_row.finished_at = datetime.now(timezone.utc)
            run_row.status = result.status
            run_row.records_fetched = result.records_fetched
            run_row.records_created = result.records_created
            run_row.records_updated = result.records_updated
            run_row.records_rejected = result.records_rejected
            run_row.errors = result.errors
            if result.status == "success":
                source_registry.last_successful_run_at = run_row.finished_at
            else:
                source_registry.last_failure_at = run_row.finished_at
            db.commit()

        return result
