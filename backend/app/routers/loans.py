import logging
from collections.abc import Sequence
from time import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.book import Book
from app.models.book_loan import BookLoan, LoanStatus
from app.models.user import User
from app.routers.dependencies import require_user
from app.schemas.book_loan import BookLoanResponse

router = APIRouter(prefix="/loans", tags=["loans"])
logger = logging.getLogger("uvicorn.error.library_api")

USER_DEPENDENCY = Depends(require_user)
DB_DEPENDENCY = Depends(get_db)


@router.get("/me", response_model=list[BookLoanResponse])
async def list_my_loans(
    user: User = USER_DEPENDENCY, db: AsyncSession = DB_DEPENDENCY
) -> Sequence[BookLoan]:
    loans = (
        await db.scalars(
            select(BookLoan)
            .where(
                BookLoan.user_id == user.id,
                BookLoan.status == LoanStatus.BORROWED,
            )
            .order_by(BookLoan.loan_timestamp.desc())
        )
    ).all()
    logger.debug("my_loans_listed user_id=%s loan_count=%s", user.id, len(loans))
    return loans


@router.post("/{loan_id}/return", response_model=BookLoanResponse)
async def return_loan(
    loan_id: int,
    user: User = USER_DEPENDENCY,
    db: AsyncSession = DB_DEPENDENCY,
) -> BookLoan:
    loan = await db.scalar(select(BookLoan).where(BookLoan.id == loan_id))
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    book = await db.scalar(
        select(Book).where(Book.id == loan.book_id).with_for_update()
    )
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Loan book no longer exists"
        )

    loan = await db.scalar(
        select(BookLoan).where(BookLoan.id == loan_id).with_for_update()
    )
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )
    if loan.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Loan belongs to another user",
        )
    if loan.status != LoanStatus.BORROWED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Loan already returned"
        )

    loan.status = LoanStatus.RETURNED
    loan.returned_timestamp = int(time())
    book.available_copies += 1
    await db.commit()
    await db.refresh(loan)
    return loan
