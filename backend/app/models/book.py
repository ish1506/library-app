from sqlalchemy import BigInteger, CheckConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("isbn", name="uq_books_isbn"),
        CheckConstraint(
            "loan_duration_days >= 1", name="ck_books_loan_duration_days_positive"
        ),
        CheckConstraint("total_copies >= 0", name="ck_books_total_copies_nonnegative"),
        CheckConstraint(
            "available_copies >= 0", name="ck_books_available_copies_nonnegative"
        ),
        CheckConstraint(
            "available_copies <= total_copies",
            name="ck_books_available_copies_lte_total_copies",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[int] = mapped_column(BigInteger, nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False)
    loan_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False)
