"""invitations refer to users by alias

Revision ID: dcbfb8860b7a
Revises: 6d339f52f632
Create Date: 2024-01-21 13:07:50.310286

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision: str = "dcbfb8860b7a"
down_revision: Union[str, None] = "6d339f52f632"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with Session(bind=op.get_bind()) as session:
        session.execute(sa.delete(sa.table("invitations")))
    op.add_column("invitations", sa.Column("addressee_alias", sa.String(length=64), nullable=False))
    op.drop_column("invitations", "addressee_id")


def downgrade() -> None:
    with Session(bind=op.get_bind()) as session:
        session.execute(sa.delete(sa.table("invitations")))
    op.add_column("invitations", sa.Column("addressee_id", sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column("invitations", "addressee_alias")
