# -*- coding: utf-8 -*-
"""Refresh size command.
"""
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from omoide.commands.refresh_size.cfg import Config
from omoide.commands.refresh_size.main import Pack
from omoide.commands.refresh_size.main import get_metainfo
from omoide.commands.refresh_size.main import update_size
from omoide.storage.database import models


def main(
        engine: Engine,
        config: Config,
) -> None:
    """Refresh disk usage for every item."""
    path = None

    if Path(config.hot_folder).exists():
        path = Path(config.hot_folder)

    elif Path(config.cold_folder).exists():
        path = Path(config.cold_folder)

    if not path:
        raise RuntimeError('No actual folder to work with')

    print(f'Config: {config}')
    changed = 0
    last_meta = None
    with Session(engine) as session:
        for i, pack in enumerate(get_metainfo(config, session), start=1):
            target = Pack(*pack)
            metainfo = session.query(models.Metainfo).get(target.uuid)

            if metainfo is None:
                print(f'Cannot find metainfo {target.uuid}')
                continue

            changed += update_size(config, metainfo, target, path)
            session.commit()
            print(f'\rChanged {i} items ({changed} operations)', end='')
            last_meta = metainfo.item_uuid

        print(f'\nLast record: {last_meta}')
