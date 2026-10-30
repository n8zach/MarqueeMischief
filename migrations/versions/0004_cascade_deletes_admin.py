"""Cascade deletes through every foreign key and add administrators.

Revision ID: 0004_cascade_deletes_admin
Revises: 0003_daily_game_date
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_cascade_deletes_admin"
down_revision = "0003_daily_game_date"
branch_labels = None
depends_on = None

# (table, column, referred table, referred column)
FOREIGN_KEYS = [
    ("games", "puzzleId", "puzzles", "id"),
    ("answers", "userId", "users", "id"),
    ("answers", "puzzleId", "puzzles", "id"),
    ("answers", "gameId", "games", "id"),
    ("votes", "userId", "users", "id"),
    ("votes", "answerId", "answers", "id"),
    ("votes", "gameId", "games", "id"),
]


def _foreign_keys(table, column):
    return [
        fk for fk in sa.inspect(op.get_bind()).get_foreign_keys(table)
        if fk["constrained_columns"] == [column]
    ]


def _replace_foreign_key(table, column, referred_table, referred_column, ondelete):
    existing = _foreign_keys(table, column)
    if len(existing) == 1 and (existing[0].get("options", {}).get("ondelete") or None) == ondelete:
        return  # already done by an earlier, partially completed run
    for fk in existing:
        op.drop_constraint(fk["name"], table, type_="foreignkey")
    op.create_foreign_key(
        f"fk_{table}_{column}", table, referred_table, [column], [referred_column], ondelete=ondelete
    )


def _delete_orphans(table, column, referred_table, referred_column):
    # Rows pointing at a parent that no longer exists are already invalid and block the new key.
    # FOREIGN_KEYS is ordered parents-first, so rows orphaned by these deletes are removed by a later pass.
    result = op.get_bind().execute(sa.text(
        f"DELETE FROM `{table}` WHERE `{column}` IS NOT NULL "
        f"AND `{column}` NOT IN (SELECT `{referred_column}` FROM `{referred_table}`)"
    ))
    if result.rowcount:
        print(f"Removed {result.rowcount} orphaned row(s) from {table}.{column}")


def upgrade():
    for table, column, referred_table, referred_column in FOREIGN_KEYS:
        _delete_orphans(table, column, referred_table, referred_column)
        _replace_foreign_key(table, column, referred_table, referred_column, ondelete="CASCADE")

    # Codes that no longer exist already lock their users out; clear them so the key can be added.
    op.execute(
        "UPDATE users SET authorizationCode = NULL WHERE authorizationCode IS NOT NULL "
        "AND authorizationCode NOT IN (SELECT code FROM authorization_codes)"
    )
    _replace_foreign_key("users", "authorizationCode", "authorization_codes", "code", ondelete="SET NULL")
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if "isAdministrator" not in columns:
        op.add_column(
            "users",
            sa.Column("isAdministrator", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("users")}
    if "isAdministrator" in columns:
        op.drop_column("users", "isAdministrator")
    for fk in _foreign_keys("users", "authorizationCode"):
        op.drop_constraint(fk["name"], "users", type_="foreignkey")
    for fk in FOREIGN_KEYS:
        _replace_foreign_key(*fk, ondelete=None)
