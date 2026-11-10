"""restore the shared local corpus after ownership was removed"""

from typing import Sequence, Union

from alembic import op


revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, Sequence[str], None] = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The corpus configuration is local instance state, not account state. If
    # an older database lost its config during the ownership migration, restore
    # the corpus that owns the papers already present in that database.
    op.execute(
        """
        INSERT INTO corpus_configs
            (name, source, categories, document_limit, sort_by, sort_order,
             start_date, end_date)
        SELECT
            'Local research corpus', 'arxiv',
            ARRAY['cs.CL', 'cs.IR', 'cs.LG']::varchar[], 500,
            'submittedDate', 'descending', DATE '1990-01-01', CURRENT_DATE
        WHERE NOT EXISTS (SELECT 1 FROM corpus_configs)
        """
    )
    op.execute(
        """
        INSERT INTO corpus_documents (corpus_id, document_id)
        SELECT corpus.id, documents.id
        FROM corpus_configs AS corpus
        CROSS JOIN documents
        ON CONFLICT (corpus_id, document_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM corpus_documents")
    op.execute("DELETE FROM corpus_configs")
