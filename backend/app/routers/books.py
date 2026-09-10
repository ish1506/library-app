import logging
from collections.abc import Sequence
from time import time

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.book import Book
from app.models.book_loan import BookLoan, LoanStatus
from app.models.user import User
from app.routers.dependencies import get_current_user, require_admin, require_user
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.schemas.book_loan import BookLoanResponse

router = APIRouter(prefix="/books", tags=["books"])
logger = logging.getLogger("uvicorn.error.library_api")

ADMIN_DEPENDENCY = Depends(require_admin)
CURRENT_USER_DEPENDENCY = Depends(get_current_user)
USER_DEPENDENCY = Depends(require_user)
DB_DEPENDENCY = Depends(get_db)


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


@router.get("", response_model=list[BookResponse])
async def list_books(
    _user: User = CURRENT_USER_DEPENDENCY, db: AsyncSession = DB_DEPENDENCY
) -> Sequence[Book]:
    return (await db.scalars(select(Book).order_by(Book.id))).all()


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
        checked_out_copies = book.total_copies - book.available_copies
        minimum_total_copies = max(active_loan_count, checked_out_copies)
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
    if book.available_copies <= 0:
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
    return loan


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
                BookLoan.status == LoanStatus.BORROWED,
            )
            .order_by(BookLoan.loan_timestamp.desc())
        )
    ).all()
