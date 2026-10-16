"""Record the schema that existed before authorization-code registration.

Revision ID: 0001_existing_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_existing_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=True),
        sa.Column("password", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "puzzles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=256), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("puzzleId", sa.Integer(), nullable=False),
        sa.Column("durationSeconds", sa.Integer(), nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False),
        sa.Column("startTime", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["puzzleId"], ["puzzles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("userId", sa.Integer(), nullable=True),
        sa.Column("puzzleId", sa.Integer(), nullable=True),
        sa.Column("gameId", sa.Integer(), nullable=True),
        sa.Column("text", sa.String(length=256), nullable=True),
        sa.ForeignKeyConstraint(["gameId"], ["games.id"]),
        sa.ForeignKeyConstraint(["puzzleId"], ["puzzles.id"]),
        sa.ForeignKeyConstraint(["userId"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "votes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("userId", sa.Integer(), nullable=True),
        sa.Column("answerId", sa.Integer(), nullable=True),
        sa.Column("gameId", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["answerId"], ["answers.id"]),
        sa.ForeignKeyConstraint(["gameId"], ["games.id"]),
        sa.ForeignKeyConstraint(["userId"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("votes")
    op.drop_table("answers")
    op.drop_table("games")
    op.drop_table("puzzles")
    op.drop_table("users")
