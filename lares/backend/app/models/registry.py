import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import LicenceStatus, SourceTier


class SourceRegistry(Base, UUIDPKMixin, TimestampMixin):
    """One row per adapter/source configuration. See lares/SOURCES.md."""

    __tablename__ = "source_registry"

    name: Mapped[str] = mapped_column(String(255), unique=True)
    tier: Mapped[int] = mapped_column(Integer, default=SourceTier.TIER_4_OPEN_WEB.value)
    root_domain: Mapped[str | None] = mapped_column(String(255))
    data_categories: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    geography: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    access_method: Mapped[str | None] = mapped_column(String(128))
    update_cadence: Mapped[str | None] = mapped_column(String(64))
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    required_credential_env: Mapped[str | None] = mapped_column(String(128))

    licence_status: Mapped[str] = mapped_column(String(32), default=LicenceStatus.DISCOVERY_ONLY.value)
    attribution_required: Mapped[bool] = mapped_column(Boolean, default=False)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    licence_notes: Mapped[str | None] = mapped_column(Text)
    licence_reviewed_by: Mapped[str | None] = mapped_column(String(255))
    licence_reviewed_at: Mapped[datetime | None] = mapped_column()

    rate_limit_notes: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    last_successful_run_at: Mapped[datetime | None] = mapped_column()
    last_failure_at: Mapped[datetime | None] = mapped_column()
    reliability_score: Mapped[int | None] = mapped_column(Integer)


class IngestionRun(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ingestion_run"

    source_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_registry.id"), index=True
    )
    started_at: Mapped[datetime] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    status: Mapped[str] = mapped_column(String(32), default="running")  # running|success|partial|failed
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_created: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[str] | None] = mapped_column(JSONB)
    retries: Mapped[int] = mapped_column(Integer, default=0)
