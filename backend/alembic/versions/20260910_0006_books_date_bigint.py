"""store book publication timestamps as bigint

Revision ID: 20260910_0006
Revises: 20260910_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0006"
down_revision: str | Sequence[str] | None = "20260910_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "books",
        "date",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "books",
        "date",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
