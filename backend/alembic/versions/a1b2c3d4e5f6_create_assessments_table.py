"""create assessments table

Revision ID: a1b2c3d4e5f6
Revises: 25866b5c8498
Create Date: 2026-11-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '25866b5c8498'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('pregnancy_id', sa.Integer(), nullable=True),
        sa.Column('age', sa.Float(), nullable=False),
        sa.Column('sbp', sa.Float(), nullable=False),
        sa.Column('dbp', sa.Float(), nullable=False),
        sa.Column('temp_f', sa.Float(), nullable=False),
        sa.Column('hr', sa.Float(), nullable=False),
        sa.Column('bmi', sa.Float(), nullable=False),
        sa.Column('risk_category', sa.String(length=10), nullable=False),
        sa.Column('prob_high', sa.Float(), nullable=False),
        sa.Column('prob_low', sa.Float(), nullable=False),
        sa.Column('prob_mid', sa.Float(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['pregnancy_id'], ['pregnancy_profiles.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_id'), 'assessments', ['id'], unique=False)
    op.create_index(op.f('ix_assessments_patient_id'), 'assessments', ['patient_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_assessments_patient_id'), table_name='assessments')
    op.drop_index(op.f('ix_assessments_id'), table_name='assessments')
    op.drop_table('assessments')
