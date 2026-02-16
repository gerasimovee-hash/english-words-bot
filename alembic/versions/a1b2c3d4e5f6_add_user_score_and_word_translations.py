"""add user score and word translations

Revision ID: a1b2c3d4e5f6
Revises: 0597ff9bda20
Create Date: 2026-02-16 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "0597ff9bda20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("score", sa.Integer, nullable=False, server_default="0"))
    op.add_column("words", sa.Column("translations", sa.JSON, nullable=True))

    # Migrate existing translation data into translations list
    op.execute(
        "UPDATE words SET translations = json_build_array(translation) WHERE translation != ''"
    )


def downgrade() -> None:
    op.drop_column("words", "translations")
    op.drop_column("users", "score")
