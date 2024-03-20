"""Add room_id column to orders table

Revision ID: 2aae965676de
Revises: 65a1829d32d0
Create Date: 2023-12-26 02:04:19.125293

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2aae965676de"
down_revision: Union[str, None] = "65a1829d32d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("orders", sa.Column("room_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "orders_room_id_fkey", "orders", "rooms", ["room_id"], ["id"], onupdate="CASCADE", ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("orders_room_id_fkey", "orders", type_="foreignkey")
    op.drop_column("orders", "room_id")
    # ### end Alembic commands ###
