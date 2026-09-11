import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(enum.IntEnum):
    RESERVATION_READY = 1


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("type IN (1)", name="ck_notifications_type_valid"),
        Index(
            "ix_notifications_user_unread_created",
            "user_id",
            "read_at_timestamp",
            text("created_at_timestamp DESC"),
        ),
        Index(
            "uq_notifications_reservation_ready",
            "reservation_id",
            unique=True,
            postgresql_where=text("type = 1 AND reservation_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id", name="fk_notifications_user_id_users", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    reservation_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "book_reservations.id",
            name="fk_notifications_reservation_id_book_reservations",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    created_at_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    read_at_timestamp: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    type: Mapped[NotificationType] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
