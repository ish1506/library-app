from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.book import Book
from app.models.user import User
from app.routers.dependencies import require_admin
from app.schemas.book import BookCreate, BookResponse, BookUpdate

router = APIRouter(prefix="/books", tags=["books"])

ADMIN_DEPENDENCY = Depends(require_admin)
DB_DEPENDENCY = Depends(get_db)


def isbn_conflict(error: IntegrityError) -> bool:
    return (
        getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        == "uq_books_isbn"
    )


@router.get("", response_model=list[BookResponse])
async def list_books(
    _admin: User = ADMIN_DEPENDENCY, db: AsyncSession = DB_DEPENDENCY
) -> Sequence[Book]:
    return (await db.scalars(select(Book).order_by(Book.id))).all()


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    _admin: User = ADMIN_DEPENDENCY,
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
    return book


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    payload: BookUpdate,
    _admin: User = ADMIN_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Book:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    updates = payload.model_dump(exclude_unset=True)
    if "total_copies" in updates and updates["total_copies"] < book.available_copies:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="total_copies cannot be less than available_copies",
        )
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
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    _admin: User = ADMIN_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> Response:
    book = await db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    await db.delete(book)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
