import enum

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LoanStatus(enum.IntEnum):
    BORROWED = 1
    RETURNED = 2


class BookLoan(Base):
    __tablename__ = "book_loans"
    __table_args__ = (
        CheckConstraint("status IN (1, 2)", name="ck_book_loans_status_valid"),
        CheckConstraint(
            "due_at_timestamp >= loan_timestamp",
            name="ck_book_loans_due_at_after_loan",
        ),
        CheckConstraint(
            "(status = 1 AND returned_timestamp IS NULL) OR "
            "(status = 2 AND returned_timestamp IS NOT NULL)",
            name="ck_book_loans_lifecycle_consistent",
        ),
        Index(
            "uq_book_loans_active_user_book",
            "user_id",
            "book_id",
            unique=True,
            postgresql_where="status = 1",
        ),
        Index(
            "ix_book_loans_active_user_timestamp",
            "user_id",
            text("loan_timestamp DESC"),
            postgresql_where="status = 1",
        ),
        Index(
            "ix_book_loans_active_book_timestamp",
            "book_id",
            text("loan_timestamp DESC"),
            postgresql_where="status = 1",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", name="fk_book_loans_book_id_books"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_book_loans_user_id_users"), nullable=False
    )
    loan_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    due_at_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    returned_timestamp: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[LoanStatus] = mapped_column(
        Integer, nullable=False, default=LoanStatus.BORROWED
    )
