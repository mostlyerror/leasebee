"""add confidence summary fields to leases

Revision ID: 004_lease_confidence
Revises: 003_correction_fields
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_lease_confidence'
down_revision = '003_correction_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('leases', sa.Column('avg_confidence', sa.Float(), nullable=True))
    op.add_column('leases', sa.Column('low_confidence_count', sa.Integer(), nullable=True))
    op.add_column('leases', sa.Column('min_confidence', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('leases', 'min_confidence')
    op.drop_column('leases', 'low_confidence_count')
    op.drop_column('leases', 'avg_confidence')
