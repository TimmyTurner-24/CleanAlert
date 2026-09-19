"""Initial CleanAlert schema for a fresh deployment."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("email", sa.String(120), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("img", sa.String(60), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "report",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("date_posted", sa.DateTime(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("img", sa.String(60), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )


def downgrade():
    op.drop_table("report")
    op.drop_table("users")
