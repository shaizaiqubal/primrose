"""add corpus ingestion tables and arxiv timestamps"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8b2e5d5b6c91"
down_revision: Union[str, Sequence[str], None] = "b7a2b2ab029c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("arxiv_updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "corpus_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("categories", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("document_limit", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("sort_by", sa.String(length=32), nullable=False, server_default="submittedDate"),
        sa.Column("sort_order", sa.String(length=16), nullable=False, server_default="ascending"),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("last_synced", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]), sa.PrimaryKeyConstraint("id"),
    )
    op.create_unique_constraint("uq_corpus_config_user", "corpus_configs", ["user_id"])
    op.create_table(
        "corpus_documents",
        sa.Column("corpus_id", sa.Integer(), nullable=False), sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["corpus_id"], ["corpus_configs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("corpus_id", "document_id"),
    )
    op.create_table(
        "corpus_syncs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False), sa.Column("corpus_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("papers_discovered", sa.Integer(), nullable=False), sa.Column("papers_inserted", sa.Integer(), nullable=False),
        sa.Column("existing_papers_skipped", sa.Integer(), nullable=False), sa.Column("processing_jobs_enqueued", sa.Integer(), nullable=False),
        sa.Column("errors_encountered", sa.Integer(), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True), sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("upper_cutoff", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["corpus_id"], ["corpus_configs.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corpus_syncs_corpus_id", "corpus_syncs", ["corpus_id"])


def downgrade() -> None:
    op.drop_index("ix_corpus_syncs_corpus_id", table_name="corpus_syncs")
    op.drop_table("corpus_syncs")
    op.drop_table("corpus_documents")
    op.drop_constraint("uq_corpus_config_user", "corpus_configs", type_="unique")
    op.drop_table("corpus_configs")
    op.drop_column("documents", "arxiv_updated_at")
    op.drop_column("documents", "submitted_at")

