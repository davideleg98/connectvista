import uuid
from datetime import date

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import SignalType, VerificationState


class Project(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "project"

    name: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    infrastructure_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_asset.id"), nullable=True, index=True
    )
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    capex_eur_estimate: Mapped[int | None] = mapped_column()
    funding_source: Mapped[str | None] = mapped_column(String(255))  # e.g. "EU CEF", "national"
    announced_at: Mapped[date | None] = mapped_column()
    expected_completion: Mapped[date | None] = mapped_column()
    status: Mapped[str | None] = mapped_column(String(64))


class ProcurementNotice(Base, UUIDPKMixin, TimestampMixin):
    """A TED (or national) tender. See ONTOLOGY.md / spec §18."""

    __tablename__ = "procurement_notice"

    ted_notice_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(1024))
    contracting_authority_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    infrastructure_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_asset.id"), nullable=True, index=True
    )
    cpv_codes: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    security_relevance_category: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(2))
    value_eur_estimate: Mapped[int | None] = mapped_column()
    published_at: Mapped[date | None] = mapped_column()
    deadline_at: Mapped[date | None] = mapped_column()
    contract_duration_months: Mapped[int | None] = mapped_column(Integer)
    awarded_to_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True
    )
    award_value_eur: Mapped[int | None] = mapped_column()
    possible_renewal_date: Mapped[date | None] = mapped_column()
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source.id"), nullable=True)


class Signal(Base, UUIDPKMixin, TimestampMixin):
    """A 'why now' fact. Decays over time — see decayed_confidence in enrichment/relevance.py."""

    __tablename__ = "signal"

    signal_type: Mapped[str] = mapped_column(String(64), default=SignalType.OTHER.value, index=True)
    event_date: Mapped[date | None] = mapped_column()
    detected_at: Mapped[date | None] = mapped_column()
    infrastructure_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_asset.id"), nullable=True, index=True
    )
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    commercial_relevance_note: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    verification_state: Mapped[str] = mapped_column(
        String(32), default=VerificationState.UNVERIFIED.value
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source.id"), nullable=True)
    half_life_days: Mapped[int] = mapped_column(Integer, default=180)
