from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BookRating(Base):
    __tablename__ = "book_ratings"
    __table_args__ = (
        CheckConstraint(
            "rating IN (1, 2, 3, 4, 5)", name="ck_book_ratings_rating_valid"
        ),
        Index(
            "uq_book_ratings_user_book",
            "user_id",
            "book_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", name="fk_book_ratings_book_id_books"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", name="fk_book_ratings_user_id_users"), nullable=False
    )
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
