"""Add per-account sync selection."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_ad_account_sync_enabled"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ad_accounts")}
    if "sync_enabled" in columns:
        return

    with op.batch_alter_table("ad_accounts") as batch_op:
        batch_op.add_column(
            sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default=sa.false())
        )
    op.execute(
        "UPDATE ad_accounts "
        "SET sync_enabled = CASE WHEN is_default = 1 THEN 1 ELSE 0 END"
    )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ad_accounts")}
    if "sync_enabled" not in columns:
        return

    with op.batch_alter_table("ad_accounts") as batch_op:
        batch_op.drop_column("sync_enabled")
