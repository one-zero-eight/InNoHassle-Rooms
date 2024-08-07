"""Fix executors keys

Revision ID: 0ebe95bd6b25
Revises: de71cfac0ab1
Create Date: 2024-08-08 14:06:18.842558

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0ebe95bd6b25"
down_revision: Union[str, None] = "de71cfac0ab1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("executors_order_id_order_number_key", "executors", type_="unique")
    # ### end Alembic commands ###
    op.drop_constraint("executors_pkey", "executors", type_="primary")
    op.create_primary_key("executors_pkey", "executors", ["order_id", "order_number"])


def downgrade() -> None:
    op.drop_constraint("executors_pkey", "executors", type_="primary")
    op.create_primary_key("executors_pkey", "executors", ["user_id", "order_id", "order_number"])
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("executors_order_id_order_number_key", "executors", ["order_id", "order_number"])
    # ### end Alembic commands ###
