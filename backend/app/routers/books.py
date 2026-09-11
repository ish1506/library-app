import logging
from collections.abc import Sequence
from time import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import desc, func, literal_column, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.book import Book
from app.models.book_loan import BookLoan, LoanStatus
from app.models.book_reservation import BookReservation, ReservationStatus
from app.models.user import User
from app.routers.dependencies import get_current_user, require_admin, require_user
from app.schemas.book import BookCreate, BookListQuery, BookResponse, BookUpdate
from app.schemas.book_loan import BookLoanResponse
from app.schemas.book_reservation import BookReservationResponse
from app.services.reservations import (
    active_counts,
    expire_ready_reservations,
    timestamp,
)

router = APIRouter(prefix="/books", tags=["books"])
logger = logging.getLogger("uvicorn.error.library_api")

ADMIN_DEPENDENCY = Depends(require_admin)
CURRENT_USER_DEPENDENCY = Depends(get_current_user)
USER_DEPENDENCY = Depends(require_user)
DB_DEPENDENCY = Depends(get_db)


def book_search_vector():
    return func.setweight(
        func.to_tsvector("simple", Book.title), literal_column("'A'")
    ).op("||")(
        func.setweight(func.to_tsvector("simple", Book.author), literal_column("'B'"))
    )


def isbn_conflict(error: IntegrityError) -> bool:
    return (
        getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        == "uq_books_isbn"
    )


def loan_history_conflict(error: IntegrityError) -> bool:
    return (
        getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        == "fk_book_loans_book_id_books"
    )


def reservation_conflict(error: IntegrityError) -> bool:
    return (
        getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        == "fk_book_reservations_book_id_books"
    )


@router.get("", response_model=list[BookResponse])
async def list_books(
    query: Annotated[BookListQuery, Query()],
    _user: User = CURRENT_USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Sequence[Book]:
    statement = select(Book)
    if query.q is not None:
        search_vector = book_search_vector()
        statement = statement.where(
            search_vector.op("@@")(func.websearch_to_tsquery("simple", query.q))
        )
    if query.date_from is not None:
        statement = statement.where(Book.date >= query.date_from)
    if query.date_to is not None:
        statement = statement.where(Book.date <= query.date_to)

    if query.q is not None:
        statement = statement.order_by(
            desc(
                func.ts_rank_cd(
                    book_search_vector(),
                    func.websearch_to_tsquery("simple", query.q),
                )
            ),
            Book.id,
        )
    else:
        statement = statement.order_by(Book.id)
    return (await db.scalars(statement)).all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    _user: User = CURRENT_USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Book:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return book


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    payload: BookCreate,
    _admin: User = ADMIN_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Book:
    book = Book(**payload.model_dump(), available_copies=payload.total_copies)
    db.add(book)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        if isbn_conflict(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists"
            ) from error
        raise
    await db.refresh(book)
    logger.debug("book_created book_id=%s", book.id)
    return book


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    _admin: User = ADMIN_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Book:
    book = await db.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    updates = payload.model_dump(exclude_unset=True)
    await expire_ready_reservations(db, book)
    if "total_copies" in updates:
        active_loan_count = (
            await db.scalar(
                select(func.count(BookLoan.id)).where(
                    BookLoan.book_id == book_id,
                    BookLoan.status == LoanStatus.BORROWED,
                )
            )
            or 0
        )
        ready_reservation_count = (
            await db.scalar(
                select(func.count(BookReservation.id)).where(
                    BookReservation.book_id == book_id,
                    BookReservation.status == ReservationStatus.READY,
                )
            )
            or 0
        )
        checked_out_copies = book.total_copies - book.available_copies
        minimum_total_copies = max(
            active_loan_count + ready_reservation_count, checked_out_copies
        )
        if updates["total_copies"] < minimum_total_copies:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="total_copies cannot be reduced below checked-out copies",
            )
        copies_delta = updates["total_copies"] - book.total_copies
        updates["available_copies"] = book.available_copies + copies_delta
    for field, value in updates.items():
        setattr(book, field, value)

    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        if isbn_conflict(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="ISBN already exists"
            ) from error
        raise
    await db.refresh(book)
    logger.debug("book_updated book_id=%s", book.id)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    _admin: User = ADMIN_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Response:
    book = await db.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    await db.delete(book)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        if loan_history_conflict(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book has loan history and cannot be deleted",
            ) from error
        if reservation_conflict(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book has reservations and cannot be deleted",
            ) from error
        raise
    logger.debug("book_deleted book_id=%s", book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{book_id}/loans",
    response_model=BookLoanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def borrow_book(
    book_id: int,
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> BookLoan:
    book = await db.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    await expire_ready_reservations(db, book)
    if book.available_copies <= 0:
        await db.commit()
        logger.info(
            "book_borrow_rejected book_id=%s user_id=%s reason=unavailable",
            book_id,
            user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Book is unavailable"
        )
    active_loan = await db.scalar(
        select(BookLoan).where(
            BookLoan.book_id == book_id,
            BookLoan.user_id == user.id,
            BookLoan.status == LoanStatus.BORROWED,
        )
    )
    if active_loan is not None:
        await db.commit()
        logger.info(
            "book_borrow_rejected book_id=%s user_id=%s reason=active_loan loan_id=%s",
            book_id,
            user.id,
            active_loan.id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active loan already exists",
        )

    now = int(time())
    loan = BookLoan(
        book_id=book_id,
        user_id=user.id,
        loan_timestamp=now,
        due_at_timestamp=now + book.loan_duration_days * 86_400,
        status=LoanStatus.BORROWED,
    )
    book.available_copies -= 1
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    logger.info(
        "book_borrowed book_id=%s user_id=%s loan_id=%s",
        book_id,
        user.id,
        loan.id,
    )
    return loan


@router.post(
    "/{book_id}/reservations",
    response_model=BookReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reserve_book(
    book_id: int,
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> BookReservation:
    book = await db.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    now = timestamp()
    await expire_ready_reservations(db, book, now)
    if book.available_copies > 0:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Book is available"
        )
    active_loan, active_reservations, _ = await active_counts(db, book_id)
    if (
        await db.scalar(
            select(BookLoan).where(
                BookLoan.book_id == book_id,
                BookLoan.user_id == user.id,
                BookLoan.status == LoanStatus.BORROWED,
            )
        )
        is not None
    ):
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Active loan already exists"
        )
    if (
        await db.scalar(
            select(BookReservation).where(
                BookReservation.book_id == book_id,
                BookReservation.user_id == user.id,
                BookReservation.status.in_(
                    (ReservationStatus.PENDING, ReservationStatus.READY)
                ),
            )
        )
        is not None
    ):
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active reservation already exists",
        )
    if active_reservations >= active_loan:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Reservation queue is full"
        )
    reservation = BookReservation(
        book_id=book_id,
        user_id=user.id,
        created_at_timestamp=now,
        status=ReservationStatus.PENDING,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    logger.info(
        "reservation_created reservation_id=%s book_id=%s user_id=%s",
        reservation.id,
        book_id,
        user.id,
    )
    return reservation


@router.get("/{book_id}/loans", response_model=list[BookLoanResponse])
async def list_book_loans(
    book_id: int,
    _admin: User = ADMIN_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Sequence[BookLoan]:
    if (
        await db.scalar(select(Book).where(Book.id == book_id).with_for_update())
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return (
        await db.scalars(
            select(BookLoan)
            .where(
                BookLoan.book_id == book_id,
            )
            .order_by(BookLoan.loan_timestamp.desc())
        )
    ).all()
