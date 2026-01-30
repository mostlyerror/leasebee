"""Add metadata field to extractions table

Revision ID: 001_add_metadata
Revises:
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_metadata'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add metadata JSONB column to extractions table."""
    op.add_column('extractions', sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade():
    """Remove metadata column from extractions table."""
    op.drop_column('extractions', 'metadata')
