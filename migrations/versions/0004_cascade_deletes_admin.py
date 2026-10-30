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


def _replace_foreign_key(table, column, referred_table, referred_column, ondelete):
    for fk in sa.inspect(op.get_bind()).get_foreign_keys(table):
        if fk["constrained_columns"] == [column]:
            op.drop_constraint(fk["name"], table, type_="foreignkey")
    op.create_foreign_key(
        f"fk_{table}_{column}", table, referred_table, [column], [referred_column], ondelete=ondelete
    )


def upgrade():
    for fk in FOREIGN_KEYS:
        _replace_foreign_key(*fk, ondelete="CASCADE")

    # Codes that no longer exist already lock their users out; clear them so the key can be added.
    op.execute(
        "UPDATE users SET authorizationCode = NULL WHERE authorizationCode IS NOT NULL "
        "AND authorizationCode NOT IN (SELECT code FROM authorization_codes)"
    )
    op.create_foreign_key(
        "fk_users_authorizationCode", "users", "authorization_codes",
        ["authorizationCode"], ["code"], ondelete="SET NULL",
    )
    op.add_column(
        "users",
        sa.Column("isAdministrator", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("users", "isAdministrator")
    op.drop_constraint("fk_users_authorizationCode", "users", type_="foreignkey")
    for fk in FOREIGN_KEYS:
        _replace_foreign_key(*fk, ondelete=None)
