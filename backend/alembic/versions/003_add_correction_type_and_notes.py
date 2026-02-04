"""add correction_type and notes to field_corrections

Revision ID: 003_correction_fields
Revises: 002_add_multi_tenant_models
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_correction_fields'
down_revision = '002_add_multi_tenant_models'
branch_labels = None
depends_on = None


def upgrade():
    # Add correction_type and notes columns to field_corrections table
    op.add_column('field_corrections', sa.Column('correction_type', sa.String(), nullable=True))
    op.add_column('field_corrections', sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    # Remove correction_type and notes columns
    op.drop_column('field_corrections', 'notes')
    op.drop_column('field_corrections', 'correction_type')
