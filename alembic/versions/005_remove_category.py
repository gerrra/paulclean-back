"""Remove category field from services table

Revision ID: 005
Revises: 001
Create Date: 2025-08-28 17:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "003"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.drop_column("services", "category")

def downgrade() -> None:
    op.add_column("services", sa.Column("category", sa.String(), nullable=False, server_default="other"))
