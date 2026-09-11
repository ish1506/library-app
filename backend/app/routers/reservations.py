import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.book import Book
from app.models.book_reservation import BookReservation, ReservationStatus
from app.models.user import User
from app.routers.dependencies import require_user
from app.schemas.book_reservation import (
    BookReservationResponse,
    ReservationConfirmationResponse,
)
from app.services.reservations import (
    create_loan_for_ready_reservation,
    expire_ready_reservations,
    release_reservation,
    timestamp,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])
logger = logging.getLogger("uvicorn.error.library_api")
USER_DEPENDENCY = Depends(require_user)
DB_DEPENDENCY = Depends(get_db)


@router.get("/me", response_model=list[BookReservationResponse])
async def list_my_reservations(
    limit: int = Query(default=50, ge=1, le=100),
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> list[BookReservation]:
    return (
        await db.scalars(
            select(BookReservation)
            .where(BookReservation.user_id == user.id)
            .order_by(
                BookReservation.created_at_timestamp.desc(), BookReservation.id.desc()
            )
            .limit(limit)
        )
    ).all()


@router.post(
    "/{reservation_id}/confirm", response_model=ReservationConfirmationResponse
)
async def confirm_reservation(
    reservation_id: int,
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> dict:
    reservation = await db.scalar(
        select(BookReservation).where(
            BookReservation.id == reservation_id, BookReservation.user_id == user.id
        )
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
        )
    book = await db.scalar(
        select(Book).where(Book.id == reservation.book_id).with_for_update()
    )
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation book no longer exists",
        )
    reservation = await db.scalar(
        select(BookReservation)
        .where(BookReservation.id == reservation_id, BookReservation.user_id == user.id)
        .with_for_update()
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
        )
    now = timestamp()
    await expire_ready_reservations(db, book, now)
    if (
        reservation.status != ReservationStatus.READY
        or (reservation.expires_at_timestamp or 0) <= now
    ):
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Reservation is not ready"
        )
    try:
        loan = await create_loan_for_ready_reservation(
            db, book, reservation, user.id, now
        )
        await db.commit()
    except ValueError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    await db.refresh(loan)
    logger.info(
        "reservation_fulfilled reservation_id=%s book_id=%s user_id=%s",
        reservation.id,
        book.id,
        user.id,
    )
    return {
        "reservation": BookReservationResponse.model_validate(reservation),
        "loan": loan,
    }


@router.delete("/{reservation_id}", response_model=BookReservationResponse)
async def cancel_reservation(
    reservation_id: int,
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> BookReservation:
    reservation = await db.scalar(
        select(BookReservation).where(
            BookReservation.id == reservation_id, BookReservation.user_id == user.id
        )
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
        )
    book = await db.scalar(
        select(Book).where(Book.id == reservation.book_id).with_for_update()
    )
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation book no longer exists",
        )
    reservation = await db.scalar(
        select(BookReservation)
        .where(BookReservation.id == reservation_id, BookReservation.user_id == user.id)
        .with_for_update()
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
        )
    now = timestamp()
    await expire_ready_reservations(db, book, now)
    if reservation.status not in (ReservationStatus.PENDING, ReservationStatus.READY):
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation is already terminal",
        )
    await release_reservation(db, book, reservation, now)
    await db.commit()
    await db.refresh(reservation)
    return reservation
