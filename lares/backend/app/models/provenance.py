import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import VerificationState


class Source(Base, UUIDPKMixin, TimestampMixin):
    """One row per origin document/dataset instance (not per domain)."""

    __tablename__ = "source"

    source_registry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_registry.id"), nullable=True
    )
    publisher: Mapped[str | None] = mapped_column(String(512))
    title: Mapped[str | None] = mapped_column(String(1024))
    url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[date | None] = mapped_column()
    retrieved_at: Mapped[datetime | None] = mapped_column()
    content_hash: Mapped[str | None] = mapped_column(String(64))
    raw_excerpt: Mapped[str | None] = mapped_column(Text)

    evidences: Mapped[list["Evidence"]] = relationship(back_populates="source")


class Claim(Base, UUIDPKMixin, TimestampMixin):
    """A raw, possibly-contradicting assertion. See ONTOLOGY.md."""

    __tablename__ = "claim"

    subject_type: Mapped[str] = mapped_column(String(64), index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    predicate: Mapped[str] = mapped_column(String(64), index=True)
    object_type: Mapped[str | None] = mapped_column(String(64))
    object_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    object_literal: Mapped[str | None] = mapped_column(Text)

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    verification_state: Mapped[str] = mapped_column(
        String(32), default=VerificationState.UNVERIFIED.value
    )
    extra: Mapped[dict | None] = mapped_column(JSONB)

    evidences: Mapped[list["Evidence"]] = relationship(back_populates="claim")


class Evidence(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "evidence"

    claim_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("claim.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("source.id"), index=True)
    excerpt: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str] = mapped_column(String(32), default="manual")

    claim: Mapped["Claim"] = relationship(back_populates="evidences")
    source: Mapped["Source"] = relationship(back_populates="evidences")
