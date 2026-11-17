"""Add hospitals, alerts and outcomes tables.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "hospitals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("address", sa.String(255)),
        sa.Column("contact_number", sa.String(20)),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("facility_level", sa.String(50), server_default="PHC"),
        sa.Column("has_blood_bank", sa.Boolean(), server_default=sa.false()),
        sa.Column("has_nicu", sa.Boolean(), server_default=sa.false()),
        sa.Column("has_csection", sa.Boolean(), server_default=sa.false()),
    )
    op.create_index("ix_hospitals_district", "hospitals", ["district"])
    op.create_index("ix_hospitals_id", "hospitals", ["id"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("message", sa.String(255), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])
    op.create_table(
        "outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referral_id", sa.Integer(), sa.ForeignKey("referrals.id"), nullable=False),
        sa.UniqueConstraint("referral_id", name="uq_outcomes_referral_id"),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("delivery_outcome", sa.String(100), nullable=False),
        sa.Column("notes", sa.String(500)),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_outcomes_id", "outcomes", ["id"])

def downgrade():
    op.drop_index("ix_outcomes_id", table_name="outcomes")
    op.drop_table("outcomes")
    op.drop_index("ix_alerts_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_hospitals_id", table_name="hospitals")
    op.drop_index("ix_hospitals_district", table_name="hospitals")
    op.drop_table("hospitals")
