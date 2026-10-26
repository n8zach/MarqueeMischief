"""Identify daily games by their local calendar date.

Revision ID: 0003_daily_game_date
Revises: 0002_authorization_codes
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_daily_game_date"
down_revision = "0002_authorization_codes"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("games", sa.Column("dailyDate", sa.Date(), nullable=True))
    op.create_unique_constraint("uq_games_daily_date", "games", ["dailyDate"])


def downgrade():
    op.drop_constraint("uq_games_daily_date", "games", type_="unique")
    op.drop_column("games", "dailyDate")
