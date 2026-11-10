"""track corpus synchronization stages and entity processing"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9a0b1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("entities_processed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "corpus_syncs",
        sa.Column("stage", sa.String(length=32), nullable=False, server_default="queued"),
    )
    op.execute("UPDATE corpus_syncs SET stage = 'completed' WHERE status = 'completed'")
    op.execute("UPDATE corpus_syncs SET stage = 'failed' WHERE status = 'failed'")


def downgrade() -> None:
    op.drop_column("corpus_syncs", "stage")
    op.drop_column("documents", "entities_processed")
