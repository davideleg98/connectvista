import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class Role(Base, UUIDPKMixin, TimestampMixin):
    """An organisational buying function, independent of any named person."""

    __tablename__ = "role"

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), index=True
    )
    role_category: Mapped[str] = mapped_column(String(64))  # CSO|head_of_security|procurement|...
    title_as_seen: Mapped[str | None] = mapped_column(String(255))
    is_filled: Mapped[bool] = mapped_column(default=False)


class Person(Base, UUIDPKMixin, TimestampMixin):
    """Public professional identity only. Never fabricated contact info."""

    __tablename__ = "person"

    full_name: Mapped[str] = mapped_column(String(255))
    public_role_title: Mapped[str | None] = mapped_column(String(255))
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("role.id"), nullable=True)
    role_category: Mapped[str | None] = mapped_column(String(64))
    public_profile_url: Mapped[str | None] = mapped_column(Text)
    public_corporate_contact: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[date | None] = mapped_column()
