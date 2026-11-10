"""cascade delete document topic assignments with their documents

Revision ID: a464dad944ea
Revises: 0a1b2c3d4e5f
Create Date: 2026-11-10 11:58:23.202821

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a464dad944ea'
down_revision: Union[str, Sequence[str], None] = '0a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f('document_topics_id_fkey'), 'document_topics', type_='foreignkey')
    op.create_foreign_key(
        'document_topics_id_fkey',
        'document_topics',
        'documents',
        ['id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('document_topics_id_fkey', 'document_topics', type_='foreignkey')
    op.create_foreign_key(
        'document_topics_id_fkey',
        'document_topics',
        'documents',
        ['id'],
        ['id'],
    )