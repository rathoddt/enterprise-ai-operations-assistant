"""add updated_at to assistant request events

Revision ID: 100960c0ff49
Revises: 903564ffc547
Create Date: 2026-11-12 16:16:18.454731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '100960c0ff49'
down_revision: Union[str, Sequence[str], None] = '903564ffc547'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Add updated_at to assistant_request_events."""
    op.add_column(
        "assistant_request_events",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Remove updated_at from assistant_request_events."""
    op.drop_column(
        "assistant_request_events",
        "updated_at",
    )

