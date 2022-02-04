from typing import Type, Optional, Tuple
from gettext import gettext as _

from maubot import Plugin
from maubot.handlers import command
from maubot.matrix import MaubotMessageEvent
from mautrix.util.config.proxy import BaseProxyConfig
from mautrix.client.client import Client
from mautrix.types import UserID, RoomCreatePreset, EventID
from sqlalchemy.exc import IntegrityError

from .db import CommunityDatabase
from .utils import CommunityConfig, emoji_argument
from . import models


class CommunityPlugin(Plugin):
    db: CommunityDatabase
    config: CommunityConfig

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return CommunityConfig

    async def start(self) -> None:
        self.on_external_config_update()
        self.db = CommunityDatabase(self.database, self.loader, self.config)

    def on_external_config_update(self) -> None:
        self.config.load_and_update()

    async def _send_direct_message(self, to: UserID, body: str) -> EventID:
        room_obj = self.db.directroom.get_for_mxid(to)
        if not room_obj:
            room = await self.client.create_room(
                preset=RoomCreatePreset.TRUSTED_PRIVATE, invitees=[to], is_direct=True
            )
            self.db.directroom.set_direct_room(to, room)
        else:
            room = room_obj.room_id
            members = await self.client.get_joined_members(room)
            if to not in members:
                await self.client.invite_user(room, to)
        return await self.client.send_text(room, body)

    def is_superuser(self, mxid: str) -> bool:
        return mxid in self.config.get("superusers", [])

    @command.new(name="roles", help=_("Get your assigned roles in a private message"))
    @command.argument(
        "user",
        "user ID",
        required=False,
        parser=lambda val: Client.parse_user_id(val) if val else None,
    )
    async def roles(
        self, evt: MaubotMessageEvent, user: Optional[Tuple[str, str]]
    ) -> None:
        if user is not None:
            if not self.db.user.from_mxid(evt.sender).has_perm("get", "role"):
                await evt.reply(_("You do not have the permission to do this"))
                return
            mxid = UserID(f"@{user[0]}:{user[1]}")
        else:
            mxid = evt.sender
        roles = self.db.user.get_roles(str(mxid))
        if user is not None:
            roles_txt = _("User {mxid} has the following roles").format(mxid=mxid)
        else:
            roles_txt = _("You have the following roles:\n")
        cur_category = None
        for role in roles:
            if role.category != cur_category:
                roles_txt += f"{role.category.name}:\n"
                cur_category = role.category
            roles_txt += f"- {role.name}\n"
        await self._send_direct_message(evt.sender, roles_txt)

    @command.new(name="role_category", require_subcommand=True)
    async def role_category(self, evt: MaubotMessageEvent):
        pass

    async def create_rolecategory(
        self,
        evt: MaubotMessageEvent,
        name: str,
        admin_role: str,
        parent: Optional[str],
        transient: bool,
    ):

        if not self.db.user.from_mxid(evt.sender).has_perm("add", "rolecategory"):
            await evt.reply(_("You do not have the permission to do this"))
            return
        author = self.db.user.get_or_create(matrix_id=evt.sender)
        author_roles = self.db.user.get_roles(evt.sender)
        parent_category = None
        if parent:
            parent_category = self.db.rolecategory.get(name=parent)
            if not parent_category:
                await evt.reply(
                    _("Category {category} not " "found").format(category=parent)
                )
                return
            if parent_category.admin_role not in author_roles and not self.is_superuser(
                evt.sender
            ):
                await evt.reply(
                    _(
                        "You must be in the {role} role to add children to the "
                        "{category} category"
                    ).format(role=parent_category.admin_role, category=parent_category)
                )
                return
        new_admin_role = self.db.role.get(name=admin_role)
        if not new_admin_role:
            await evt.reply(_("The role {role} does not exist").format(role=admin_role))
            return
        if new_admin_role not in author_roles and not self.is_superuser(evt.sender):
            await evt.reply(
                _("You must be in the {role} role to add a new category").format(
                    role=new_admin_role
                )
            )
            return

        try:
            self.db.rolecategory.create(
                name, new_admin_role, parent_category, transient, author
            )
        except IntegrityError:
            self.db.session.rollback()
            await evt.reply(
                _("The role category {category} already exists.").format(category=name)
            )
            return
        await evt.reply(
            _("The role category {category} has been created").format(category=name)
        )

    @role_category.subcommand(name="add", help=_("Create a new role category"))
    @command.argument("name", "category name")
    @command.argument("admin_role", "admin role name")
    @command.argument("parent", "parent category name", required=False)
    async def role_category_add(
        self, evt: MaubotMessageEvent, name: str, admin_role: str, parent: Optional[str]
    ):
        await self.create_rolecategory(evt, name, admin_role, parent, False)

    @role_category.subcommand(
        name="add_transient", help=_("Create a new transient role category")
    )
    @command.argument("name", "category name")
    @command.argument("admin_role", "admin role name")
    @command.argument("parent", "parent category name", required=False)
    async def role_category_add_transient(
        self, evt: MaubotMessageEvent, name: str, admin_role: str, parent: Optional[str]
    ):
        await self.create_rolecategory(evt, name, admin_role, parent, True)

    @command.new(name="role", require_subcommand=True)
    async def role(self, evt: MaubotMessageEvent):
        pass

    @role.subcommand(name="add", help=_("Create a new role"))
    @command.argument("name", "role name")
    @command.argument("emoji", parser=emoji_argument)
    @command.argument("category", "category name")
    async def role_add(
        self, evt: MaubotMessageEvent, name: str, emoji: str, category: Optional[str]
    ):
        if not self.db.user.from_mxid(evt.sender).has_perm("add", "role"):
            await evt.reply(_("You do not have the permission to do this"))
            return
        author = self.db.user.get_or_create(matrix_id=evt.sender)
        author_roles = self.db.user.get_roles(evt.sender)
        parent_category = self.db.rolecategory.get(name=category)
        if not parent_category:
            await evt.reply(
                _("Category {category} not found").format(category=category)
            )
            return
        if parent_category.admin_role not in author_roles and not self.is_superuser(
            evt.sender
        ):
            await evt.reply(
                _(
                    "You must be in the {role} role to add a role in the {category}"
                    "category"
                ).format(role=parent_category.admin_role, category=parent_category)
            )
            return

        try:
            self.db.role.create(name, emoji, parent_category, author)
        except IntegrityError as e:
            self.db.session.rollback()
            if "role.name" in str(e):
                await evt.reply(_("The role {role} already exists").format(role=name))
                return
            elif "role.emoji" in str(e):
                await evt.reply(
                    _(
                        "A role already has the emoji {emoji} in the same category"
                    ).format(emoji=emoji)
                )
                return
            raise e
        await evt.reply(_("The role {role} has been created").format(role=name))
