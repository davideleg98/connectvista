"""sensitivity geometry trigger

Enforces DATA_GOVERNANCE.md's geometry-precision-by-sensitivity rule at the
database layer (not just in application code), so it can't be bypassed by an
API bug: STANDARD keeps exact geometry, ELEVATED snaps to a ~0.005 degree
grid (~500m) and is tagged 'approximate', RESTRICTED_PUBLIC snaps to a
~0.1 degree grid (~11km, administrative-centroid-scale) and is tagged
'administrative_centroid'.

Revision ID: bf8f0f581ce5
Revises: 8aa1b5cadfc9
Create Date: 2026-09-25
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "bf8f0f581ce5"
down_revision = "8aa1b5cadfc9"
branch_labels = None
depends_on = None

TABLES = [
    "infrastructure_asset",
    "physical_site",
    "infrastructure_network",
    "infrastructure_cluster",
]

FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION enforce_sensitivity_geometry() RETURNS trigger AS $$
BEGIN
    IF NEW.geom IS NULL THEN
        RETURN NEW;
    END IF;

    IF NEW.sensitivity_level = 'RESTRICTED_PUBLIC' THEN
        NEW.geom := ST_SnapToGrid(NEW.geom, 0.1);
        NEW.geometry_precision := 'administrative_centroid';
    ELSIF NEW.sensitivity_level = 'ELEVATED' THEN
        NEW.geom := ST_SnapToGrid(NEW.geom, 0.005);
        NEW.geometry_precision := 'approximate';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

DROP_FUNCTION_SQL = "DROP FUNCTION IF EXISTS enforce_sensitivity_geometry() CASCADE;"


def upgrade() -> None:
    op.execute(FUNCTION_SQL)
    for table in TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_enforce_sensitivity_geometry_{table}
            BEFORE INSERT OR UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION enforce_sensitivity_geometry();
            """
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_enforce_sensitivity_geometry_{table} ON {table};")
    op.execute(DROP_FUNCTION_SQL)
