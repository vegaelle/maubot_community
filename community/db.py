from typing import Optional, Type, TypeVar
import tempfile
import os

from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker, Session
from maubot.loader import BasePluginLoader
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext

from . import models
from .utils import CommunityConfig


T = TypeVar("T", bound=Type[models.Base])


def wrap_model(cls: T, db: "CommunityDatabase") -> T:
    cls._db = db
    return cls


class CommunityDatabase:

    db: Engine

    def __init__(
        self, db: Optional[Engine], loader: BasePluginLoader, config: CommunityConfig
    ) -> None:
        assert db, "Database must be enabled for this plugin"
        self.db = db
        self.loader = loader
        self.config = config
        self.alembic_cfg = Config()
        Session = sessionmaker(bind=db)
        self.session = Session()
        self.user = wrap_model(models.User, db=self)
        self.directroom = wrap_model(models.DirectRoom, db=self)
        self.auditlog = wrap_model(models.AuditLog, db=self)
        self.permission = wrap_model(models.Permission, db=self)
        self.rolecategory = wrap_model(models.RoleCategory, db=self)
        self.role = wrap_model(models.Role, db=self)
        self.rolemenu = wrap_model(models.RoleMenu, db=self)
        self.userrole = wrap_model(models.UserRole, db=self)
        self.space = wrap_model(models.Space, db=self)
        self.room = wrap_model(models.Room, db=self)
        self.rolepermission = wrap_model(models.RolePermission, db=self)
        # self.promotion = wrap_model(models.Promotion, db=self)

        with tempfile.TemporaryDirectory() as tmpdirname:

            for file in self.loader.sync_list_files("community/alembic/versions"):
                with open(
                    os.path.join(tmpdirname, os.path.basename(file)), mode="wb"
                ) as fd:
                    fd.write(self.loader.sync_read_file(file))

            # for file in self.loader.sync_list_files(
            #     "community/alembic/versions/__pycache__"
            # ):
            #     with open(
            #         os.path.join(tmpdirname, "__pycache__", os.path.basename(file)),
            #         mode="wb",
            #     ) as fd:
            #         fd.write(self.loader.sync_read_file(file))

            self.alembic_cfg.set_main_option("version_locations", tmpdirname)
            # self.alembic_cfg.set_main_option("version_locations", tmpdirname + ':' +
            #                                  '../alembic/versions')
            # self.alembic_cfg.set_main_option("version_path_separator", ':')
            self.alembic_cfg.set_main_option("script_location", "alembic")
            self.alembic_cfg.set_main_option("sqlalchemy.url", str(db.url))

            script = ScriptDirectory.from_config(self.alembic_cfg)
            revision = "head"

            def upgrade(rev, _):
                return script._upgrade_revs(revision, rev)

            with EnvironmentContext(
                self.alembic_cfg,
                script,
                fn=upgrade,
                as_sql=False,
                starting_rev=None,
                destination_rev=revision,
                tag=None,
            ):
                from .alembic import env
