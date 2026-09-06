"""lead_events: append-only history of state changes

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

lead_state = postgresql.ENUM("PENDING", "REACHED_OUT", name="lead_state", create_type=False)


def upgrade() -> None:
    op.create_table(
        "lead_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lead_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_state", lead_state, nullable=True),
        sa.Column("to_state", lead_state, nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_email", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_lead_events_lead_id_created_at", "lead_events", ["lead_id", "created_at"])

    # Backfill: every existing lead was submitted, and the reached-out ones were moved once.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO lead_events
                (id, lead_id, from_state, to_state, actor_id, actor_email, created_at)
            SELECT gen_random_uuid(), id, NULL, 'PENDING', NULL, NULL, created_at FROM leads
            """
        )
    )
    bind.execute(
        sa.text(
            """
            INSERT INTO lead_events
                (id, lead_id, from_state, to_state, actor_id, actor_email, created_at)
            SELECT gen_random_uuid(), l.id, 'PENDING', 'REACHED_OUT', l.reached_out_by, u.email,
                   COALESCE(l.reached_out_at, l.updated_at)
            FROM leads l LEFT JOIN users u ON u.id = l.reached_out_by
            WHERE l.state = 'REACHED_OUT'
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_lead_events_lead_id_created_at", table_name="lead_events")
    op.drop_table("lead_events")
