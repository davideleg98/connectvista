import uuid
from datetime import date

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import VerificationState


class Relationship(Base, UUIDPKMixin, TimestampMixin):
    """The resolved, published graph edge. See ONTOLOGY.md for the claim vs.
    relationship distinction — this is the "current best" view; `claim` keeps
    every raw, possibly-contradicting assertion.
    """

    __tablename__ = "relationship"

    subject_type: Mapped[str] = mapped_column(String(64), index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    predicate: Mapped[str] = mapped_column(String(64), index=True)
    object_type: Mapped[str] = mapped_column(String(64), index=True)
    object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)

    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source.id"), nullable=True)
    claim_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("claim.id"), nullable=True)

    confidence: Mapped[int] = mapped_column(Integer, default=0)
    verification_state: Mapped[str] = mapped_column(
        String(32), default=VerificationState.UNVERIFIED.value
    )
    first_seen: Mapped[date | None] = mapped_column()
    last_seen: Mapped[date | None] = mapped_column()
    valid_from: Mapped[date | None] = mapped_column()
    valid_to: Mapped[date | None] = mapped_column()
