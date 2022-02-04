"""First table version

Revision ID: ee77025817ec
Revises: 
Create Date: 2022-02-02 19:32:22.870232

"""
from datetime import datetime, timezone
from itertools import count

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = "ee77025817ec"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=30), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("emoji", sa.String(length=8), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"], ["rolecategory.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "emoji", name="unique_emoji_in_category"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "rolecategory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=30), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("admin_role_id", sa.Integer(), nullable=True),
        sa.Column("transient", sa.Boolean(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["admin_role_id"], ["role.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["rolecategory.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("matrix_id", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matrix_id"),
    )
    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=30), nullable=True),
        sa.Column("args", sa.Text(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "directroom",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=30), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rolemenu",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"], ["rolecategory.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "room",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("internal_id", sa.String(length=100), nullable=True),
        sa.Column("recommended", sa.Boolean(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image", sa.String(length=100), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum("public", "space", "private", name="visibility"),
            nullable=True,
        ),
        sa.Column("required_role_id", sa.Integer(), nullable=True),
        sa.Column("admin_commands", sa.Boolean(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["required_role_id"], ["role.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rolepermission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permission.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "space",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("internal_id", sa.String(length=100), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("welcome_room_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image", sa.String(length=100), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum("public", "space", "private", name="visibility"),
            nullable=True,
        ),
        sa.Column("required_role_id", sa.Integer(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["space.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["required_role_id"], ["role.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["welcome_room_id"], ["room.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "userrole",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("space_id", sa.Integer(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["space_id"], ["space.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # Creation of initial data

    permission_table = table(
        "permission",
        column("id", sa.Integer),
        column("model", sa.String(50)),
        column("action", sa.String(30)),
        column("creation_date", sa.DateTime),
        column(
            "created_by_id",
            sa.Integer,
            sa.ForeignKey("user.id", ondelete="RESTRICT"),
        ),
    )
    now = datetime.now(timezone.utc)
    permissions = []
    c = count(1)
    for model in (
        "role",
        "rolecategory",
        "user",
        "auditlog",
        "directroom",
        "permission",
        "room",
        "rolepermission",
        "space",
        "userrole",
    ):
        actions = [
            {
                "id": next(c),
                "model": model,
                "action": action,
                "creation_date": now,
                "created_by_id": None,
            }
            for action in ("create", "read", "update", "delete")
        ]
        permissions += actions
    op.bulk_insert(permission_table, permissions)
    
    role_table = table(
        "role",
        column("id", sa.Integer),
        column("name", sa.String(50)),
        column("category_id", sa.Integer),
        column("active", sa.Boolean),
        column("emoji", sa.String(30)),
        column("creation_date", sa.DateTime),
        column(
            "created_by_id",
            sa.Integer,
            sa.ForeignKey("user.id", ondelete="RESTRICT"),
        ),
    )
    op.bulk_insert(role_table, [{
        'id': 1,
        'name': 'superadmins',
        'category_id': None,
        'active': True,
        'emoji': '✳️',
        'creation_date': now,
        'created_by_id': None,
    }])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("userrole")
    op.drop_table("space")
    op.drop_table("rolepermission")
    op.drop_table("room")
    op.drop_table("permission")
    op.drop_table("directroom")
    op.drop_table("auditlog")
    op.drop_table("user")
    op.drop_table("rolecategory")
    op.drop_table("role")
    # ### end Alembic commands ###
