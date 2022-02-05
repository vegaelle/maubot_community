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
from .utils import CommunityConfig, emoji_argument, arguments, Argument
from . import validators, models


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
    async def role_category(self, _: MaubotMessageEvent):
        pass

    async def create_rolecategory(
        self,
        evt: MaubotMessageEvent,
        name: str,
        admin_role: models.Role,
        parent: Optional[models.RoleCategory],
        transient: bool,
    ):

        author = self.db.user.get_or_create(matrix_id=evt.sender)
        try:
            self.db.rolecategory.create(
                name, admin_role, parent, transient, author
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
    @arguments(
        "add_rolecategory",
        name=Argument("category name"),
        admin_role=Argument(
            "admin role name", validator=validators.valid_author_role
        ),
        parent=Argument(
            "parent category name",
            required=False,
            validator=validators.valid_rolecategory,
        ),
    )
    async def role_category_add(
        self, evt: MaubotMessageEvent, name: str, admin_role: models.Role, parent:
        Optional[models.RoleCategory]
    ):
        await self.create_rolecategory(evt, name, admin_role, parent, False)

    @role_category.subcommand(
        name="add_transient", help=_("Create a new transient role category")
    )
    @arguments(
        "add_rolecategory",
        name=Argument("category name"),
        admin_role=Argument(
            "admin role name", validator=validators.valid_author_role
        ),
        parent=Argument(
            "parent category name",
            required=False,
            validator=validators.valid_rolecategory,
        ),
    )
    async def role_category_add_transient(
        self, evt: MaubotMessageEvent, name: str, admin_role: models.Role, parent:
        Optional[models.RoleCategory]
    ):
        await self.create_rolecategory(evt, name, admin_role, parent, True)

    @command.new(name="role", require_subcommand=True)
    async def role(self, _: MaubotMessageEvent):
        pass

    @role.subcommand(name="add", help=_("Create a new role"))
    @arguments(
        "add_role",
        name=Argument("role name"),
        emoji=Argument(
            parser=emoji_argument
        ),
        category=Argument(
            required=False,
            validator=validators.valid_rolecategory,
        ),
    )
    async def role_add(
        self, evt: MaubotMessageEvent, name: str, emoji: str, category:
        Optional[models.RoleCategory]
    ):
        author = self.db.user.get_or_create(matrix_id=evt.sender)

        try:
            self.db.role.create(name, emoji, category, author)
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
