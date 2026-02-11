"""add prompt_templates table

Revision ID: 005_prompt_templates
Revises: 004_lease_confidence
Create Date: 2026-02-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_prompt_templates'
down_revision = '004_lease_confidence'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('version', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('field_type_guidance', sa.Text(), nullable=False),
        sa.Column('extraction_examples', sa.Text(), nullable=False),
        sa.Column('null_value_guidance', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('avg_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_prompt_templates_version', 'prompt_templates', ['version'])
    op.create_index('ix_prompt_templates_is_active', 'prompt_templates', ['is_active'])


def downgrade():
    op.drop_index('ix_prompt_templates_is_active')
    op.drop_index('ix_prompt_templates_version')
    op.drop_table('prompt_templates')
