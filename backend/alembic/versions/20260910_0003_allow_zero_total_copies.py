"""allow books with zero total copies

Revision ID: 20260910_0003
Revises: 20260910_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260910_0003"
down_revision: str | Sequence[str] | None = "20260910_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_books_total_copies_positive", "books", type_="check")
    op.create_check_constraint(
        "ck_books_total_copies_nonnegative", "books", "total_copies >= 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_books_total_copies_nonnegative", "books", type_="check")
    op.create_check_constraint("ck_books_total_copies_positive", "books", "total_copies >= 1")
