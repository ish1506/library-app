import enum

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReservationStatus(enum.IntEnum):
    PENDING = 1
    READY = 2
    FULFILLED = 3
    CANCELLED = 4
    EXPIRED = 5


class BookReservation(Base):
    __tablename__ = "book_reservations"
    __table_args__ = (
        CheckConstraint(
            "status IN (1, 2, 3, 4, 5)", name="ck_book_reservations_status_valid"
        ),
        CheckConstraint(
            "(status = 1 AND ready_at_timestamp IS NULL AND expires_at_timestamp IS NULL AND fulfilled_at_timestamp IS NULL AND cancelled_at_timestamp IS NULL) OR "
            "(status = 2 AND ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NULL AND cancelled_at_timestamp IS NULL) OR "
            "(status = 3 AND ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NOT NULL AND cancelled_at_timestamp IS NULL) OR "
            "(status = 4 AND cancelled_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NULL AND ((ready_at_timestamp IS NULL AND expires_at_timestamp IS NULL) OR (ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL))) OR "
            "(status = 5 AND ready_at_timestamp IS NOT NULL AND expires_at_timestamp IS NOT NULL AND fulfilled_at_timestamp IS NULL AND cancelled_at_timestamp IS NULL)",
            name="ck_book_reservations_lifecycle_consistent",
        ),
        Index(
            "uq_book_reservations_active_user_book",
            "user_id",
            "book_id",
            unique=True,
            postgresql_where=text("status IN (1, 2)"),
        ),
        Index(
            "ix_book_reservations_pending_queue",
            "book_id",
            "created_at_timestamp",
            "id",
            postgresql_where=text("status = 1"),
        ),
        Index(
            "ix_book_reservations_ready_expiry",
            "expires_at_timestamp",
            postgresql_where=text("status = 2"),
        ),
        Index("ix_book_reservations_book_status", "book_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey(
            "books.id", name="fk_book_reservations_book_id_books", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id", name="fk_book_reservations_user_id_users", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    created_at_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ready_at_timestamp: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expires_at_timestamp: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fulfilled_at_timestamp: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    cancelled_at_timestamp: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    status: Mapped[ReservationStatus] = mapped_column(Integer, nullable=False)
