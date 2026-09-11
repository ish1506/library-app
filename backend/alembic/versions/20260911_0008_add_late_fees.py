"""persist book late-fee rates and loan fees

Revision ID: 20260911_0008
Revises: 20260910_0007
"""

from collections.abc import Sequence
from time import time

import sqlalchemy as sa
from alembic import op
from app.policy import library_policy

revision: str = "20260911_0008"
down_revision: str | Sequence[str] | None = "20260911_0007"
branch_labels = None


def upgrade() -> None:
    # Importing the policy above validates it before any schema mutation.
    rate = library_policy.late_fees.daily_rate_cents
    op.add_column(
        "books",
        sa.Column(
            "late_fee_cents_per_day",
            sa.Integer(),
            nullable=False,
            server_default=str(rate),
        ),
    )
    op.add_column(
        "book_loans",
        sa.Column("late_fee_cents", sa.Integer(), nullable=False, server_default="0"),
    )

    cutoff = int(time())
    op.execute(
        sa.text(
            """
            UPDATE book_loans AS loans
            SET late_fee_cents = GREATEST(
                0,
                (
                    (CASE
                        WHEN loans.returned_timestamp IS NOT NULL
                        THEN loans.returned_timestamp
                        ELSE :cutoff
                    END) - loans.due_at_timestamp
                ) / 86400
            ) * books.late_fee_cents_per_day
            FROM books
            WHERE books.id = loans.book_id
            """
        ).bindparams(cutoff=cutoff)
    )
    op.create_check_constraint(
        "ck_books_late_fee_cents_per_day_positive",
        "books",
        "late_fee_cents_per_day > 0",
    )
    op.create_check_constraint(
        "ck_book_loans_late_fee_cents_nonnegative",
        "book_loans",
        "late_fee_cents >= 0",
    )
    op.alter_column("books", "late_fee_cents_per_day", server_default=None)
    op.alter_column("book_loans", "late_fee_cents", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "ck_book_loans_late_fee_cents_nonnegative", "book_loans", type_="check"
    )
    op.drop_constraint(
        "ck_books_late_fee_cents_per_day_positive", "books", type_="check"
    )
    op.drop_column("book_loans", "late_fee_cents")
    op.drop_column("books", "late_fee_cents_per_day")
