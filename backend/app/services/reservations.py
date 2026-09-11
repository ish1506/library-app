import logging
from time import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.book import Book
from app.models.book_loan import BookLoan, LoanStatus
from app.models.book_reservation import BookReservation, ReservationStatus
from app.models.notification import Notification, NotificationType

logger = logging.getLogger("uvicorn.error.library_api")


def timestamp() -> int:
    return int(time())


async def _next_pending(db: AsyncSession, book_id: int) -> BookReservation | None:
    return await db.scalar(
        select(BookReservation)
        .where(
            BookReservation.book_id == book_id,
            BookReservation.status == ReservationStatus.PENDING,
        )
        .order_by(BookReservation.created_at_timestamp, BookReservation.id)
        .with_for_update()
    )


async def _notify_ready(
    db: AsyncSession, reservation: BookReservation, book: Book, now: int
) -> None:
    existing = await db.scalar(
        select(Notification).where(
            Notification.reservation_id == reservation.id,
            Notification.type == NotificationType.RESERVATION_READY,
        )
    )
    if existing is not None:
        return
    db.add(
        Notification(
            user_id=reservation.user_id,
            reservation_id=reservation.id,
            created_at_timestamp=now,
            type=NotificationType.RESERVATION_READY,
            payload={
                "title": book.title,
                "author": book.author,
                "expires_at_timestamp": reservation.expires_at_timestamp,
            },
        )
    )


async def _promote_or_release(
    db: AsyncSession, book: Book, now: int
) -> BookReservation | None:
    next_reservation = await _next_pending(db, book.id)
    if next_reservation is None:
        book.available_copies += 1
        return None

    next_reservation.status = ReservationStatus.READY
    next_reservation.ready_at_timestamp = now
    next_reservation.expires_at_timestamp = now + settings.reservation_hold_seconds
    await _notify_ready(db, next_reservation, book, now)
    logger.info(
        "reservation_ready reservation_id=%s book_id=%s user_id=%s",
        next_reservation.id,
        book.id,
        next_reservation.user_id,
    )
    return next_reservation


async def expire_ready_reservations(
    db: AsyncSession, book: Book, now: int | None = None
) -> int:
    now = timestamp() if now is None else now
    expired = (
        await db.scalars(
            select(BookReservation)
            .where(
                BookReservation.book_id == book.id,
                BookReservation.status == ReservationStatus.READY,
                BookReservation.expires_at_timestamp <= now,
            )
            .order_by(BookReservation.expires_at_timestamp, BookReservation.id)
            .with_for_update()
        )
    ).all()
    for reservation in expired:
        reservation.status = ReservationStatus.EXPIRED
        await _promote_or_release(db, book, now)
        logger.info(
            "reservation_expired reservation_id=%s book_id=%s user_id=%s",
            reservation.id,
            book.id,
            reservation.user_id,
        )
    return len(expired)


async def promote_returned_copy(db: AsyncSession, book: Book, now: int) -> None:
    await expire_ready_reservations(db, book, now)
    await _promote_or_release(db, book, now)


async def release_reservation(
    db: AsyncSession, book: Book, reservation: BookReservation, now: int | None = None
) -> None:
    if reservation.status not in (ReservationStatus.PENDING, ReservationStatus.READY):
        raise ValueError("Reservation is already terminal")
    now = timestamp() if now is None else now
    was_ready = reservation.status == ReservationStatus.READY
    reservation.status = ReservationStatus.CANCELLED
    reservation.cancelled_at_timestamp = now
    if was_ready:
        await _promote_or_release(db, book, now)


async def create_loan_for_ready_reservation(
    db: AsyncSession, book: Book, reservation: BookReservation, user_id: int, now: int
) -> BookLoan:
    if reservation.status != ReservationStatus.READY:
        raise ValueError("Reservation is not ready")
    active_loan = await db.scalar(
        select(BookLoan).where(
            BookLoan.book_id == book.id,
            BookLoan.user_id == user_id,
            BookLoan.status == LoanStatus.BORROWED,
        )
    )
    if active_loan is not None:
        raise ValueError("Active loan already exists")

    loan = BookLoan(
        book_id=book.id,
        user_id=user_id,
        loan_timestamp=now,
        due_at_timestamp=now + book.loan_duration_days * 86_400,
        status=LoanStatus.BORROWED,
    )
    reservation.status = ReservationStatus.FULFILLED
    reservation.fulfilled_at_timestamp = now
    db.add(loan)
    return loan


async def active_counts(db: AsyncSession, book_id: int) -> tuple[int, int, int]:
    loan_count = await db.scalar(
        select(func.count(BookLoan.id)).where(
            BookLoan.book_id == book_id, BookLoan.status == LoanStatus.BORROWED
        )
    )
    reservation_count = await db.scalar(
        select(func.count(BookReservation.id)).where(
            BookReservation.book_id == book_id,
            BookReservation.status.in_(
                (ReservationStatus.PENDING, ReservationStatus.READY)
            ),
        )
    )
    ready_count = await db.scalar(
        select(func.count(BookReservation.id)).where(
            BookReservation.book_id == book_id,
            BookReservation.status == ReservationStatus.READY,
        )
    )
    return int(loan_count or 0), int(reservation_count or 0), int(ready_count or 0)
