import uuid
from datetime import date

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import AssetStatus, GeometryPrecision, SalesReadinessState, SensitivityLevel

# Fields allowed to be non-null when sensitivity_level == RESTRICTED_PUBLIC.
# Enforced in app/resolution/sensitivity.py at write time (see DATA_GOVERNANCE.md).
SENSITIVE_FIELD_ALLOWLIST = {
    "id",
    "canonical_name",
    "alt_names",
    "category",
    "subcategory",
    "status",
    "country",
    "region",
    "geom",
    "geometry_precision",
    "sensitivity_level",
    "operator_org_id",
    "public_authority_org_id",
    "operational_description",
    "created_at",
    "updated_at",
    "last_verified_at",
    "last_updated_at",
    "data_completeness_score",
    "sales_readiness_state",
}


class _GeoMixin:
    country: Mapped[str | None] = mapped_column(String(2), index=True)  # ISO-3166-1 alpha-2
    region: Mapped[str | None] = mapped_column(String(16))  # NUTS code where known
    municipality: Mapped[str | None] = mapped_column(String(255))
    geom = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=True
    )
    geometry_precision: Mapped[str] = mapped_column(
        String(32), default=GeometryPrecision.APPROXIMATE.value
    )
    sensitivity_level: Mapped[str] = mapped_column(String(32), default=SensitivityLevel.STANDARD.value)


class InfrastructureAsset(Base, UUIDPKMixin, TimestampMixin, _GeoMixin):
    __tablename__ = "infrastructure_asset"

    canonical_name: Mapped[str] = mapped_column(String(512), index=True)
    alt_names: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    category: Mapped[str] = mapped_column(String(64), index=True)  # energy|maritime|aviation|...
    subcategory: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default=AssetStatus.UNKNOWN.value)

    operational_description: Mapped[str | None] = mapped_column(Text)
    capacity_indicators: Mapped[dict | None] = mapped_column(JSONB)
    importance_indicators: Mapped[dict | None] = mapped_column(JSONB)

    operator_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    owner_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    ultimate_owner_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    public_authority_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True, index=True
    )
    network_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_network.id"), nullable=True, index=True
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_cluster.id"), nullable=True, index=True
    )

    # Deterministic external ids for entity resolution (spec §14)
    osm_id: Mapped[str | None] = mapped_column(String(64), index=True)
    facility_code: Mapped[str | None] = mapped_column(String(128))

    source_confidence: Mapped[int | None] = mapped_column(Integer)
    data_completeness_score: Mapped[int | None] = mapped_column(Integer)
    last_verified_at: Mapped[date | None] = mapped_column()
    last_updated_at: Mapped[date | None] = mapped_column()

    sales_readiness_state: Mapped[str] = mapped_column(
        String(32), default=SalesReadinessState.DISCOVERED.value, index=True
    )

    # Lares relevance component scores (see ONTOLOGY.md) — nullable until enrichment runs.
    strategic_importance: Mapped[int | None] = mapped_column(Integer)
    physical_complexity: Mapped[int | None] = mapped_column(Integer)
    response_complexity: Mapped[int | None] = mapped_column(Integer)
    autonomous_fit: Mapped[int | None] = mapped_column(Integer)
    security_intensity: Mapped[int | None] = mapped_column(Integer)
    buyer_accessibility: Mapped[int | None] = mapped_column(Integer)
    contactability: Mapped[int | None] = mapped_column(Integer)
    procurement_signal: Mapped[int | None] = mapped_column(Integer)
    change_signal: Mapped[int | None] = mapped_column(Integer)
    data_confidence: Mapped[int | None] = mapped_column(Integer)
    lares_fit: Mapped[int | None] = mapped_column(Integer, index=True)

    status_pipeline_stage: Mapped[str] = mapped_column(String(32), default="discovered")
    published: Mapped[bool] = mapped_column(default=False)


class PhysicalSite(Base, UUIDPKMixin, TimestampMixin, _GeoMixin):
    """A location that can host one or more assets/operators (e.g. a port terminal)."""

    __tablename__ = "physical_site"

    canonical_name: Mapped[str] = mapped_column(String(512))
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("infrastructure_cluster.id"), nullable=True, index=True
    )
    operator_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True
    )


class InfrastructureNetwork(Base, UUIDPKMixin, TimestampMixin, _GeoMixin):
    __tablename__ = "infrastructure_network"

    canonical_name: Mapped[str] = mapped_column(String(512))
    category: Mapped[str] = mapped_column(String(64))  # electricity_grid|gas_pipeline|submarine_cable|rail_corridor
    operator_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text)


class InfrastructureCluster(Base, UUIDPKMixin, TimestampMixin, _GeoMixin):
    """Groups sites operationally-one-entity-externally but distinct internally (a port, airport system)."""

    __tablename__ = "infrastructure_cluster"

    canonical_name: Mapped[str] = mapped_column(String(512))
    category: Mapped[str] = mapped_column(String(64))  # port|airport_system
    authority_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.id"), nullable=True
    )
