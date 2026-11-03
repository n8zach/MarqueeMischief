"""Give every game a shareable two-word code.

Revision ID: 0005_game_codes
Revises: 0004_cascade_deletes_admin
"""
from alembic import op
import sqlalchemy as sa

from game_codes import generate_game_code, load_words


revision = "0005_game_codes"
down_revision = "0004_cascade_deletes_admin"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("code", sa.String(length=64), nullable=True))
    connection = op.get_bind()
    games = sa.table("games", sa.column("id", sa.Integer), sa.column("code", sa.String), sa.column("dailyDate", sa.Date))
    words = load_words()
    used = set()
    for game_id, daily_date in connection.execute(sa.select(games.c.id, games.c.dailyDate)).fetchall():
        if daily_date is not None:
            code = f"DAILY{game_id}"
        else:
            code = generate_game_code(words, used)
            used.add(code)
        connection.execute(games.update().where(games.c.id == game_id).values(code=code))
    op.alter_column("games", "code", existing_type=sa.String(length=64), nullable=False)
    op.create_unique_constraint("uq_games_code", "games", ["code"])


def downgrade():
    op.drop_constraint("uq_games_code", "games", type_="unique")
    op.drop_column("games", "code")
