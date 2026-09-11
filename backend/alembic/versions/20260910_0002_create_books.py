"""create books table

Revision ID: 20260910_0002
Revises: 20260909_0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0002"
down_revision: str | Sequence[str] | None = "20260909_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("date", sa.Integer(), nullable=False),
        sa.Column("isbn", sa.String(length=13), nullable=False),
        sa.Column("loan_duration_days", sa.Integer(), nullable=False),
        sa.Column("total_copies", sa.Integer(), nullable=False),
        sa.Column("available_copies", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "loan_duration_days >= 1", name="ck_books_loan_duration_days_positive"
        ),
        sa.CheckConstraint("total_copies >= 1", name="ck_books_total_copies_positive"),
        sa.CheckConstraint(
            "available_copies >= 0", name="ck_books_available_copies_nonnegative"
        ),
        sa.CheckConstraint(
            "available_copies <= total_copies",
            name="ck_books_available_copies_lte_total_copies",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn", name="uq_books_isbn"),
    )


def downgrade() -> None:
    op.drop_table("books")
