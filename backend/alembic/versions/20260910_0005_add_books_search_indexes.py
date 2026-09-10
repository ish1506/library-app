"""add book search indexes

Revision ID: 20260910_0005
Revises: 20260910_0004
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260910_0005"
down_revision: str | Sequence[str] | None = "20260910_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX ix_books_title_author_search ON books USING gin ((
            setweight(to_tsvector('simple', title), 'A') ||
            setweight(to_tsvector('simple', author), 'B')
        ))
        """
    )
    op.create_index("ix_books_date", "books", ["date"])


def downgrade() -> None:
    op.drop_index("ix_books_date", table_name="books")
    op.drop_index("ix_books_title_author_search", table_name="books")
