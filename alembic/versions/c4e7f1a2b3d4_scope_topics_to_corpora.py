"""scope topic clusters and assignments to corpora"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e7f1a2b3d4"
down_revision: Union[str, Sequence[str], None] = "8b2e5d5b6c91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing topic assignments were generated from the global embedding set,
    # so they cannot be safely attributed to a corpus. Rebuild them on the next
    # corpus sync after changing the keys to include corpus_id.
    op.execute("DELETE FROM document_topics")
    op.execute("DELETE FROM topics")

    # The old document-to-topic foreign key depends on topics_pkey, so it must
    # be removed before replacing the topics primary key.
    op.drop_constraint("document_topics_cluster_id_fkey", "document_topics", type_="foreignkey")

    op.add_column("topics", sa.Column("corpus_id", sa.Integer(), nullable=True))
    op.alter_column("topics", "corpus_id", nullable=False)
    op.drop_constraint("topics_pkey", "topics", type_="primary")
    op.create_primary_key("topics_pkey", "topics", ["corpus_id", "cluster_id"])
    op.create_foreign_key(
        "topics_corpus_id_fkey",
        "topics",
        "corpus_configs",
        ["corpus_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.add_column("document_topics", sa.Column("corpus_id", sa.Integer(), nullable=True))
    op.execute("UPDATE document_topics SET corpus_id = 0")
    op.alter_column("document_topics", "corpus_id", nullable=False)
    op.drop_constraint("document_topics_pkey", "document_topics", type_="primary")
    op.create_primary_key("document_topics_pkey", "document_topics", ["corpus_id", "id"])
    op.create_foreign_key(
        "document_topics_corpus_id_fkey",
        "document_topics",
        "corpus_configs",
        ["corpus_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "document_topics_topic_fkey",
        "document_topics",
        "topics",
        ["corpus_id", "cluster_id"],
        ["corpus_id", "cluster_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("document_topics_topic_fkey", "document_topics", type_="foreignkey")
    op.drop_constraint("document_topics_corpus_id_fkey", "document_topics", type_="foreignkey")
    op.drop_constraint("document_topics_pkey", "document_topics", type_="primary")
    op.drop_column("document_topics", "corpus_id")
    op.create_primary_key("document_topics_pkey", "document_topics", ["id"])
    op.create_foreign_key(
        "document_topics_cluster_id_fkey",
        "document_topics",
        "topics",
        ["cluster_id"],
        ["cluster_id"],
    )

    op.drop_constraint("topics_corpus_id_fkey", "topics", type_="foreignkey")
    op.drop_constraint("topics_pkey", "topics", type_="primary")
    op.drop_column("topics", "corpus_id")
    op.create_primary_key("topics_pkey", "topics", ["cluster_id"])
