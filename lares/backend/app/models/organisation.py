import uuid
from datetime import date

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import OrganisationType, OwnershipClass


class Organisation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "organisation"

    legal_name: Mapped[str] = mapped_column(String(512), index=True)
    trading_names: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    org_type: Mapped[str] = mapped_column(String(32), default=OrganisationType.OTHER.value)
    legal_form: Mapped[str | None] = mapped_column(String(128))

    company_number: Mapped[str | None] = mapped_column(String(64), index=True)
    lei: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    vat_id: Mapped[str | None] = mapped_column(String(32))
    jurisdiction: Mapped[str | None] = mapped_column(String(2))  # ISO-3166-1 alpha-2

    website: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    hq_country: Mapped[str | None] = mapped_column(String(2))
    hq_city: Mapped[str | None] = mapped_column(String(255))

    revenue_eur_estimate: Mapped[int | None] = mapped_column()
    employee_estimate: Mapped[int | None] = mapped_column(Integer)
    ownership_class: Mapped[str] = mapped_column(String(32), default=OwnershipClass.UNKNOWN.value)

    direct_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True
    )
    ultimate_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True
    )

    data_completeness_score: Mapped[int | None] = mapped_column(Integer)
    last_verified_at: Mapped[date | None] = mapped_column()

    direct_parent: Mapped["Organisation | None"] = relationship(
        remote_side="Organisation.id", foreign_keys=[direct_parent_id]
    )

    public_authority_detail: Mapped["PublicAuthorityDetail | None"] = relationship(
        back_populates="organisation", uselist=False
    )


class PublicAuthorityDetail(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "public_authority_detail"

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), unique=True
    )
    authority_level: Mapped[str | None] = mapped_column(String(64))  # national|regional|municipal|eu
    regulatory_scope: Mapped[str | None] = mapped_column(Text)

    organisation: Mapped["Organisation"] = relationship(back_populates="public_authority_detail")
