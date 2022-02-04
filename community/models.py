import enum
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from gettext import gettext as _

from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base


if TYPE_CHECKING:
    from .db import CommunityDatabase


Base = declarative_base()


class Visibility(enum.Enum):
    public = 0
    space = 1
    private = 2


class User(Base):
    __tablename__ = "user"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    matrix_id = Column(String(100), unique=True)
    active = Column(Boolean)

    def __str__(self) -> str:
        return self.matrix_id

    @classmethod
    def get_roles(cls, mxid: str) -> list["Role"]:
        user = cls.get_or_create(matrix_id=mxid)
        if user.active:
            return user.roles
        return []

    @classmethod
    def get_or_create(cls, **kwargs) -> "User":
        instance = cls._db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance
        if "active" not in kwargs:
            kwargs["active"] = True
        instance = cls(**kwargs)
        cls._db.session.add(instance)
        cls._db.session.commit()
        return instance

    @classmethod
    def from_mxid(cls, mxid: str) -> "User":
        user = cls.get_or_create(matrix_id=mxid)
        return user

    def has_perm(self, action: str, model: str) -> bool:
        if self.matrix_id in self._db.config.get("superusers", []):
            return True
        return False


class DirectRoom(Base):
    __tablename__ = "directroom"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"), unique=True)
    user = relationship(User, backref=backref("direct_room", uselist=False))
    room_id = Column(String(100))

    def __str__(self) -> str:
        return _("direct message with {user}").format(user=self.user.matrix_id)

    @classmethod
    def set_direct_room(cls, mxid: str, room_id: str):
        user = cls._db.session.query(User).filter_by(matrix_id=mxid).first()
        instance = cls(user_id=user.id, room_id=room_id)
        cls._db.session.add(instance)
        cls._db.session.commit()

    @classmethod
    def get_for_mxid(cls, mxid: str) -> "DirectRoom":

        room = (
            cls._db.session.query(cls).join(User).filter(User.matrix_id == mxid).first()
        )
        return room


class AuditLog(Base):
    __tablename__ = "auditlog"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    author = relationship(User, backref="audit_lines")
    action = Column(String(30))
    args = Column(Text)
    creation_date = Column(DateTime)

    @classmethod
    def log(cls, mxid, action, model, args):
        pass


class Permission(Base):
    __tablename__ = "permission"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    model = Column(String(50))
    action = Column(String(30))
    creation_date = Column(DateTime)
    created_by_id = Column(
        Integer, ForeignKey("user.id", ondelete="RESTRICT"), nullable=True
    )
    created_by = relationship(User)

    def __str__(self) -> str:
        return f"{self.action}_{self.model}"

    @classmethod
    def get(cls, **kwargs) -> Optional["Permission"]:
        instance = cls._db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance


class RoleCategory(Base):
    __tablename__ = "rolecategory"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)
    parent_id = Column(
        Integer, ForeignKey("rolecategory.id", ondelete="RESTRICT"), nullable=True
    )
    parent = relationship(
        "RoleCategory", remote_side=[id], backref="children_categories"
    )
    admin_role_id = Column(Integer, ForeignKey("role.id", ondelete="SET NULL"))
    admin_role = relationship(
        "Role", foreign_keys=[admin_role_id], backref="admin_of_rolecategories"
    )
    transient = Column(Boolean)
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def create(
        cls,
        name: str,
        admin_role: "Role",
        parent: Optional["RoleCategory"],
        transient: bool,
        author: User,
    ) -> "RoleCategory":
        role_id = admin_role.id
        parent_id = parent.id if parent else None
        category = cls(
            name=name,
            admin_role_id=role_id,
            parent_id=parent_id,
            transient=transient,
            creation_date=datetime.now(timezone.utc),
            created_by=author,
        )
        cls._db.session.add(category)
        cls._db.session.commit()
        return category

    @classmethod
    def get(cls, **kwargs) -> Optional["RoleCategory"]:
        instance = cls._db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance


class Role(Base):
    __tablename__ = "role"
    __table_args__ = (
        UniqueConstraint("category_id", "emoji", name="unique_emoji_in_category"),
    )
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)
    category_id = Column(
        Integer, ForeignKey("rolecategory.id", ondelete="SET NULL"), nullable=True
    )
    category = relationship(RoleCategory, foreign_keys=[category_id], backref="roles")
    active = Column(Boolean)
    emoji = Column(String(8))
    description = Column(Text)
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get(cls, **kwargs) -> Optional["Role"]:
        instance = cls._db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance

    @classmethod
    def create(
        cls,
        name: str,
        emoji: str,
        category: Optional["RoleCategory"],
        author: User,
    ) -> "Role":
        category_id = category.id if category else None
        role = cls(
            name=name,
            emoji=emoji,
            category_id=category_id,
            active=True,
            creation_date=datetime.now(timezone.utc),
            created_by=author,
        )
        cls._db.session.add(role)
        cls._db.session.commit()
        return role


class RoleMenu(Base):
    __tablename__ = "rolemenu"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    category_id = Column(
        Integer, ForeignKey("rolecategory.id", ondelete="RESTRICT"), nullable=True
    )
    category = relationship(RoleCategory, backref="menus")
    active = Column(Boolean)
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User)

    def __str__(self) -> str:
        return _("role menu for category {category}").format(category=self.category)

    @classmethod
    def get_for_category(cls, category_name: str) -> Optional["Permission"]:
        instance = (
            cls._db.session.query(cls)
            .join(RoleCategory)
            .filter(RoleCategory.name == category_name)
            .first()
        )
        if instance:
            return instance


class UserRole(Base):
    __tablename__ = "userrole"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    user = relationship(User, foreign_keys=[user_id], backref="roles")
    space_id = Column(
        Integer, ForeignKey("space.id", ondelete="CASCADE"), nullable=True
    )
    space = relationship("Space", backref="spaces")
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User, foreign_keys=[created_by_id])


class Space(Base):
    __tablename__ = "space"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    internal_id = Column(String(100))
    parent_id = Column(
        Integer, ForeignKey("space.id", ondelete="SET NULL"), nullable=True
    )
    parent = relationship("Space", backref="children_spaces", remote_side="Space.id")
    welcome_room_id = Column(
        Integer, ForeignKey("room.id", ondelete="SET NULL"), nullable=True
    )
    welcome_room = relationship("Room", backref="welcome_room_to")
    description = Column(Text)
    image = Column(String(100))
    visibility = Column(Enum(Visibility))
    required_role_id = Column(
        Integer, ForeignKey("role.id", ondelete="SET NULL"), nullable=True
    )
    required_role = relationship(Role, backref="requirde_by_spaces")
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get(cls, **kwargs) -> Optional["Role"]:
        instance = cls._db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance


class Room(Base):
    __tablename__ = "room"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    internal_id = Column(String(100))
    space = relationship("Space", backref="rooms")
    recommended = Column(Boolean)
    description = Column(Text)
    image = Column(String(100))
    visibility = Column(Enum(Visibility))
    required_role_id = Column(
        Integer, ForeignKey("role.id", ondelete="SET NULL"), nullable=True
    )
    required_role = relationship(Role, backref="required_by_rooms")
    admin_commands = Column(Boolean)
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User)

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get(cls, **kwargs) -> Optional["Role"]:
        instance = cls._db.session.query(cls).filter_by(**kwargs).first()
        if instance:
            return instance


class RolePermission(Base):
    __tablename__ = "rolepermission"
    _db: "CommunityDatabase"

    id = Column(Integer, primary_key=True)
    permission_id = Column(Integer, ForeignKey("permission.id", ondelete="CASCADE"))
    permission = relationship(Permission, backref="permissions")
    creation_date = Column(DateTime)
    created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
    created_by = relationship(User)


# class Confirmation(Base):
#     __tablename__ = "confirmation"
#     _db: "CommunityDatabase"

#     id = Column(Integer, primary_key=True)
#     permission_id = Column(
#         Integer, ForeignKey("permission.id", ondelete="RESTRICT")
#     )
#     permission = relationship(Permission)
#     object = Column(String(30))
#     args = Column(String(100))
#     active = Column(Boolean)
#     creation_date = Column(DateTime)
#     created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
#     created_by = relationship(User)


# class Promotion(Base):
#     __tablename__ = "promotion"
#     _db: "CommunityDatabase"

#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
#     user = relationship(User, backref="promotions", foreign_keys=[user_id])
#     end_date = Column(DateTime)
#     duration = Column(String(10))
#     creation_date = Column(DateTime)
#     created_by_id = Column(Integer, ForeignKey("user.id", ondelete="RESTRICT"))
#     created_by = relationship(User, foreign_keys=[created_by_id])
