import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class Watchlist(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "watchlist"

    name: Mapped[str] = mapped_column(String(255))
    owner_email: Mapped[str | None] = mapped_column(String(255))


class WatchlistItem(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "watchlist_item"

    watchlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("watchlist.id"), index=True)
    item_type: Mapped[str] = mapped_column(String(64))  # infrastructure|organisation|category|country
    item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    item_value: Mapped[str | None] = mapped_column(String(255))  # for category/country watches


class Interaction(Base, UUIDPKMixin, TimestampMixin):
    """A recorded outreach action against an infrastructure or organisation."""

    __tablename__ = "interaction"

    subject_type: Mapped[str] = mapped_column(String(64))  # infrastructure|organisation
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    action: Mapped[str] = mapped_column(String(64))  # mark_contacted|note|verify_claim|flag_incorrect|...
    note: Mapped[str | None] = mapped_column(Text)
    actor_email: Mapped[str | None] = mapped_column(String(255))
    occurred_at: Mapped[datetime | None] = mapped_column()


class MergeLog(Base, UUIDPKMixin, TimestampMixin):
    """Entity-resolution merge history. Losing record's claims are re-pointed, never deleted."""

    __tablename__ = "merge_log"

    entity_type: Mapped[str] = mapped_column(String(64))
    surviving_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    merged_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    merge_reason: Mapped[str | None] = mapped_column(Text)
    match_signals: Mapped[dict | None] = mapped_column(JSONB)
    merged_by: Mapped[str] = mapped_column(String(64), default="entity_resolution_pipeline")
