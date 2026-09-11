"""create reservations and notifications

Revision ID: 20260911_0007
Revises: 20260910_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260911_0007"
down_revision: str | Sequence[str] | None = "20260910_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "book_reservations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("ready_at_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("expires_at_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("fulfilled_at_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("cancelled_at_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.CheckConstraint("status IN (1, 2, 3, 4, 5)", name="ck_book_reservations_status_valid"),
        sa.CheckConstraint(
            "(status = 1 AND ready_at_timestamp IS NULL AND expires_at_timestamp IS NULL AND fulfilled_at_timestamp IS NULL AND cancelled_at_timestamp IS NULL) OR "
            "(status = 2 AND ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NULL AND cancelled_at_timestamp IS NULL) OR "
            "(status = 3 AND ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NOT NULL AND cancelled_at_timestamp IS NULL) OR "
            "(status = 4 AND cancelled_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NULL AND ((ready_at_timestamp IS NULL AND expires_at_timestamp IS NULL) OR (ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL))) OR "
            "(status = 5 AND ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NULL AND cancelled_at_timestamp IS NULL)",
            name="ck_book_reservations_lifecycle_consistent",
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], name="fk_book_reservations_book_id_books", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_book_reservations_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_book_reservations_active_user_book", "book_reservations", ["user_id", "book_id"],
        unique=True, postgresql_where=sa.text("status IN (1, 2)"),
    )
    op.create_index(
        "ix_book_reservations_pending_queue", "book_reservations",
        ["book_id", "created_at_timestamp", "id"], postgresql_where=sa.text("status = 1"),
    )
    op.create_index(
        "ix_book_reservations_ready_expiry", "book_reservations", ["expires_at_timestamp"],
        postgresql_where=sa.text("status = 2"),
    )
    op.create_index("ix_book_reservations_book_status", "book_reservations", ["book_id", "status"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=True),
        sa.Column("created_at_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("read_at_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.CheckConstraint("type IN (1)", name="ck_notifications_type_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_notifications_user_id_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["reservation_id"], ["book_reservations.id"],
            name="fk_notifications_reservation_id_book_reservations", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_unread_created", "notifications",
        ["user_id", "read_at_timestamp", sa.text("created_at_timestamp DESC")],
    )
    op.create_index(
        "uq_notifications_reservation_ready", "notifications", ["reservation_id"], unique=True,
        postgresql_where=sa.text("type = 1 AND reservation_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("book_reservations")
