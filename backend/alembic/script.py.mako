"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "${up_revision}"
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
