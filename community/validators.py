from typing import TYPE_CHECKING
from gettext import gettext as _

from maubot.matrix import MaubotMessageEvent

if TYPE_CHECKING:
    from .bot import CommunityPlugin
    from .models import Role, RoleCategory


class CommandPermissionError(Exception):
    pass


class ValidationError(ValueError):
    pass


def check_perm(bot: "CommunityPlugin", evt: MaubotMessageEvent, permission: str):
    action, model = permission.split("_", 1)
    if not bot.db.user.from_mxid(evt.sender).has_perm(action, model):
        raise CommandPermissionError()


def valid_author_role(
    bot: "CommunityPlugin", evt: MaubotMessageEvent, val: str
) -> "Role":
    author_roles = bot.db.user.get_roles(evt.sender)
    role = bot.db.role.get(name=val)
    if not role:
        raise ValidationError(_("The role {role} does not exist").format(role=val))
    if role not in author_roles and not bot.is_superuser(evt.sender):
        raise ValidationError(
            _("You must be in the {role} role to do this").format(role=val)
        )
    return role


def valid_rolecategory(
    bot: "CommunityPlugin", evt: MaubotMessageEvent, val: str
) -> "RoleCategory":
    author_roles = bot.db.user.get_roles(evt.sender)
    role_category = bot.db.rolecategory.get(name=val)
    if not role_category:
        raise ValidationError(
            _("Category {category} not " "found").format(category=val)
        )
    if role_category.admin_role not in author_roles and not bot.is_superuser(
        evt.sender
    ):
        raise ValidationError(
            _(
                "You must be in the {role} role to add children to the "
                "{category} category"
            ).format(role=role_category.admin_role, category=role_category)
        )
    return role_category
