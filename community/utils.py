from typing import Union, Dict, List, Optional

from mautrix.util.config.proxy import BaseProxyConfig
from mautrix.util.config.base import ConfigUpdateHelper
import emoji

from . import models


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
