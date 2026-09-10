"""create book loans

Revision ID: 20260910_0004
Revises: 20260910_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260910_0004"
down_revision: str | Sequence[str] | None = "20260910_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "book_loans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("loan_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("due_at_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("returned_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN (1, 2)", name="ck_book_loans_status_valid"),
        sa.CheckConstraint(
            "due_at_timestamp >= loan_timestamp",
            name="ck_book_loans_due_at_after_loan",
        ),
        sa.CheckConstraint(
            "(status = 1 AND returned_timestamp IS NULL) OR "
            "(status = 2 AND returned_timestamp IS NOT NULL)",
            name="ck_book_loans_lifecycle_consistent",
        ),
        sa.ForeignKeyConstraint(
            ["book_id"], ["books.id"], name="fk_book_loans_book_id_books"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_book_loans_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_book_loans_active_user_book",
        "book_loans",
        ["user_id", "book_id"],
        unique=True,
        postgresql_where=sa.text("status = 1"),
    )
    op.create_index(
        "ix_book_loans_active_user_timestamp",
        "book_loans",
        ["user_id", sa.text("loan_timestamp DESC")],
        postgresql_where=sa.text("status = 1"),
    )
    op.create_index(
        "ix_book_loans_active_book_timestamp",
        "book_loans",
        ["book_id", sa.text("loan_timestamp DESC")],
        postgresql_where=sa.text("status = 1"),
    )


def downgrade() -> None:
    op.drop_table("book_loans")
