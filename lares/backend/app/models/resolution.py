import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class ReviewQueueItem(Base, UUIDPKMixin, TimestampMixin):
    """Ambiguous entity-resolution matches land here instead of being
    silently auto-merged. See ONTOLOGY.md / spec §14."""

    __tablename__ = "review_queue_item"

    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    candidate_natural_key: Mapped[dict] = mapped_column(JSONB)
    candidate_fields: Mapped[dict] = mapped_column(JSONB)
    matched_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # The row actually created for the ambiguous candidate (resolver never drops
    # it) — required so an approve action knows what to merge into matched_entity_id.
    created_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    match_signals: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)  # pending|approved|rejected|merged
