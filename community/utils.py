from typing import (
    Union,
    Dict,
    List,
    Optional,
    Callable,
    TypeVar,
    Any,
    Iterable,
    Optional,
    Awaitable,
    TYPE_CHECKING
)
from functools import wraps
from gettext import gettext as _

from mautrix.util.config.proxy import BaseProxyConfig
from mautrix.util.config.base import ConfigUpdateHelper
from maubot.handlers import command
from maubot.matrix import MaubotMessageEvent
import emoji

from . import validators


if TYPE_CHECKING:
    from .bot import CommunityPlugin


T = Callable[..., Awaitable]



class CommunityConfig(BaseProxyConfig):

    language: str
    confirmation_emojis: Dict[str, str]
    admin_command_max_duration: str
    admin_command_powerlevel: int
    default_matrix_perms: Dict[str, Union[int, Dict[str, int]]]
    superusers: List[str]

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("language")
        helper.copy("confirmation_emojis")
        helper.copy("admin_command_max_duration")
        helper.copy("admin_command_powerlevel")
        helper.copy("default_matrix_perms")
        helper.copy("superusers")

    def parse_data(self) -> None:
        self.language = self["language"]
        self.confirmation_emojis = self["confirmation_emojis"]
        self.superusers = self["superusers"]


def emoji_argument(val: str) -> Optional[str]:
    return val if emoji.is_emoji(val) else None


class Argument:

    validator: Optional[Callable[["CommunityPlugin", MaubotMessageEvent, str], Any]]
    args: Iterable[Any]
    kwargs: dict[str, Any]

    def __init__(self, *args, **kwargs):
        self.validator = None
        if "validator" in kwargs:
            self.validator = kwargs.pop("validator")
        self.args = args
        self.kwargs = kwargs


def arguments(required_perm: str=None, **arguments: Argument) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        @wraps(func)
        async def decorated(self: "CommunityPlugin", evt: MaubotMessageEvent, *args, **kwargs):
            for arg_name, arg in arguments.items():
                if arg.validator:
                    if arg_name in kwargs:
                        arg_raw = kwargs[arg_name]
                        if arg.kwargs.get('required', True) or arg_raw:
                            try:
                                arg_value = arg.validator(self, evt, arg_raw)
                            except validators.ValidationError as e:
                                await evt.reply(str(e))
                                return
                        else:
                            arg_value = arg_raw
                        kwargs[arg_name] = arg_value
                    else:
                        raise ValueError(f'Missing argument: {arg_name}')
            try:
                if required_perm:
                    validators.check_perm(self, evt, required_perm)
                await func(self, evt, *args, **kwargs)
            except validators.CommandPermissionError:
                await evt.reply(_("You do not have the permission to do this"))
                return

        decorated_var = decorated  # avoiding shadowing warnings
        for arg_name, arg in reversed(arguments.items()):
            decorated_var = command.argument(arg_name, *arg.args, **arg.kwargs)(decorated_var)
        return decorated_var

    return decorator
