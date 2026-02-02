"""Add multi-tenant models (User, Organization, OrganizationMember)

Revision ID: 002_add_multi_tenant_models
Revises: 001_add_metadata_to_extractions
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_multi_tenant_models'
down_revision = '001_add_metadata'
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('is_active', sa.String(), nullable=True),
        sa.Column('is_verified', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('plan', sa.Enum('FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE', name='subscriptionplan'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_id'), 'organizations', ['id'], unique=False)
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # Create organization_members table
    op.create_table(
        'organization_members',
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'MEMBER', 'VIEWER', name='memberrole'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('organization_id', 'user_id')
    )

    # Add multi-tenant columns to leases table
    op.add_column('leases', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f('ix_leases_organization_id'), 'leases', ['organization_id'], unique=False)
    op.create_foreign_key('fk_leases_organization_id', 'leases', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    # Update uploaded_by column to UUID
    op.alter_column('leases', 'uploaded_by',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='uploaded_by::uuid',
                    existing_nullable=True)
    op.create_index(op.f('ix_leases_uploaded_by'), 'leases', ['uploaded_by'], unique=False)
    op.create_foreign_key('fk_leases_uploaded_by', 'leases', 'users', ['uploaded_by'], ['id'], ondelete='SET NULL')

    # Update corrected_by in field_corrections to UUID
    op.alter_column('field_corrections', 'corrected_by',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='corrected_by::uuid',
                    existing_nullable=True)
    op.create_index(op.f('ix_field_corrections_corrected_by'), 'field_corrections', ['corrected_by'], unique=False)
    op.create_foreign_key('fk_field_corrections_corrected_by', 'field_corrections', 'users', ['corrected_by'], ['id'], ondelete='SET NULL')

    # Update reviewed_by in extraction_feedback to UUID
    op.alter_column('extraction_feedback', 'reviewed_by',
                    type_=postgresql.UUID(as_uuid=True),
                    postgresql_using='reviewed_by::uuid',
                    existing_nullable=True)
    op.create_index(op.f('ix_extraction_feedback_reviewed_by'), 'extraction_feedback', ['reviewed_by'], unique=False)
    op.create_foreign_key('fk_extraction_feedback_reviewed_by', 'extraction_feedback', 'users', ['reviewed_by'], ['id'], ondelete='SET NULL')


def downgrade():
    # Remove foreign keys and indexes from extraction_feedback
    op.drop_constraint('fk_extraction_feedback_reviewed_by', 'extraction_feedback', type_='foreignkey')
    op.drop_index(op.f('ix_extraction_feedback_reviewed_by'), table_name='extraction_feedback')
    op.alter_column('extraction_feedback', 'reviewed_by',
                    type_=sa.String(),
                    existing_nullable=True)

    # Remove foreign keys and indexes from field_corrections
    op.drop_constraint('fk_field_corrections_corrected_by', 'field_corrections', type_='foreignkey')
    op.drop_index(op.f('ix_field_corrections_corrected_by'), table_name='field_corrections')
    op.alter_column('field_corrections', 'corrected_by',
                    type_=sa.String(),
                    existing_nullable=True)

    # Remove foreign keys and indexes from leases
    op.drop_constraint('fk_leases_uploaded_by', 'leases', type_='foreignkey')
    op.drop_index(op.f('ix_leases_uploaded_by'), table_name='leases')
    op.alter_column('leases', 'uploaded_by',
                    type_=sa.String(),
                    existing_nullable=True)

    op.drop_constraint('fk_leases_organization_id', 'leases', type_='foreignkey')
    op.drop_index(op.f('ix_leases_organization_id'), table_name='leases')
    op.drop_column('leases', 'organization_id')

    # Drop tables
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE memberrole')
    op.execute('DROP TYPE subscriptionplan')
