"""Add authorization-code registration.

Revision ID: 0002_authorization_codes
Revises: 0001_existing_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_authorization_codes"
down_revision = "0001_existing_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "authorization_codes",
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )
    op.add_column(
        "users",
        sa.Column("authorizationCode", sa.String(length=128), nullable=True),
    )


def downgrade():
    op.drop_column("users", "authorizationCode")
    op.drop_table("authorization_codes")
