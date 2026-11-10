"""baseline full schema

Revision ID: 75e48aa242ad
Revises:
Create Date: 2026-11-10 12:09:14.197228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '75e48aa242ad'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('app_settings',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('encrypted_value', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('corpus_configs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('source', sa.String(length=32), nullable=False),
    sa.Column('categories', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('document_limit', sa.Integer(), nullable=False),
    sa.Column('sort_by', sa.String(length=32), nullable=False),
    sa.Column('sort_order', sa.String(length=16), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('last_synced', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('entities',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('canonical_name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('aliases', postgresql.ARRAY(sa.String()), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('canonical_name', 'type')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('corpus_syncs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('corpus_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('stage', sa.String(length=32), nullable=False),
    sa.Column('papers_discovered', sa.Integer(), nullable=False),
    sa.Column('papers_inserted', sa.Integer(), nullable=False),
    sa.Column('existing_papers_skipped', sa.Integer(), nullable=False),
    sa.Column('processing_jobs_enqueued', sa.Integer(), nullable=False),
    sa.Column('errors_encountered', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('error_details', sa.Text(), nullable=True),
    sa.Column('upper_cutoff', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['corpus_id'], ['corpus_configs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_corpus_syncs_corpus_id'), 'corpus_syncs', ['corpus_id'], unique=False)
    op.create_table('documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('arxiv_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('abstract', sa.String(), nullable=False),
    sa.Column('authors', sa.String(), nullable=True),
    sa.Column('year_published', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('categories', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('uploaded_by', sa.Integer(), nullable=True),
    sa.Column('embedded', sa.Boolean(), nullable=False),
    sa.Column('entities_processed', sa.Boolean(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('arxiv_updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('arxiv_id')
    )
    op.create_table('email_verification_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_email_verification_tokens_user_id'), 'email_verification_tokens', ['user_id'], unique=False)
    op.create_table('refresh_tokens',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_table('topics',
    sa.Column('corpus_id', sa.Integer(), nullable=False),
    sa.Column('cluster_id', sa.Integer(), nullable=False),
    sa.Column('cluster_name', sa.String(), nullable=True),
    sa.Column('paper_count', sa.Integer(), nullable=True),
    sa.Column('centroid', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['corpus_id'], ['corpus_configs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('corpus_id', 'cluster_id')
    )
    op.create_table('bookmarks',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'document_id', name='uq_bookmark_user_document')
    )
    op.create_table('corpus_documents',
    sa.Column('corpus_id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['corpus_id'], ['corpus_configs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('corpus_id', 'document_id')
    )
    op.create_table('document_entities',
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('extractor_version', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('document_id', 'entity_id')
    )
    op.create_index(op.f('ix_document_entities_entity_id'), 'document_entities', ['entity_id'], unique=False)
    op.create_table('document_topics',
    sa.Column('corpus_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cluster_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['corpus_id', 'cluster_id'], ['topics.corpus_id', 'topics.cluster_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['corpus_id'], ['corpus_configs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['id'], ['documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('corpus_id', 'id')
    )


def downgrade() -> None:
    op.drop_table('document_topics')
    op.drop_index(op.f('ix_document_entities_entity_id'), table_name='document_entities')
    op.drop_table('document_entities')
    op.drop_table('corpus_documents')
    op.drop_table('bookmarks')
    op.drop_table('topics')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_email_verification_tokens_user_id'), table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    op.drop_table('documents')
    op.drop_index(op.f('ix_corpus_syncs_corpus_id'), table_name='corpus_syncs')
    op.drop_table('corpus_syncs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('entities')
    op.drop_table('corpus_configs')
    op.drop_table('app_settings')
