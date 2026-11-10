"""make the local corpus shared instead of user-owned"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, Sequence[str], None] = "c4e7f1a2b3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_corpus_config_user", "corpus_configs", type_="unique")
    op.drop_constraint("corpus_configs_user_id_fkey", "corpus_configs", type_="foreignkey")
    op.drop_column("corpus_configs", "user_id")


def downgrade() -> None:
    op.add_column("corpus_configs", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "corpus_configs_user_id_fkey",
        "corpus_configs",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_unique_constraint("uq_corpus_config_user", "corpus_configs", ["user_id"])
