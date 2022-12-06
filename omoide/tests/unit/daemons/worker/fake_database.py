# -*- coding: utf-8 -*-
"""Fake database."""
import contextlib
from typing import Any
from typing import Optional
from unittest import mock
from unittest.mock import MagicMock

from omoide.storage.database import models


class FakeDatabase(MagicMock):
    """Fake database."""

    def __init__(self, *args: Any, **kw: Any) -> None:
        super().__init__(*args, **kw)
        self.engine = mock.Mock()
        self.session = mock.Mock()

    @contextlib.contextmanager
    def start_session(self):
        yield self.session

    @contextlib.contextmanager
    def life_cycle(self, echo: bool):
        _ = echo
        yield self.engine

    @staticmethod
    def select_media(
            session,
            media_id: int,
    ) -> Optional[models.Media]:
        fake_meta = models.Metainfo()
        fake_item = models.Item(metainfo=fake_meta)

        if media_id == 1:
            return models.Media(
                attempts=0,
                replication={},
                item=fake_item,
            )
        elif media_id in (2, 3):
            return models.Media(
                attempts=0,
                ext='test',
                content=b'test',
                replication={},
                item=fake_item,
            )
        return None

    @staticmethod
    def select_copy_operation(
            session,
            copy_id: int,
    ) -> Optional[models.ManualCopy]:
        if copy_id in (1, 2, 3, 5):
            return models.ManualCopy(id=copy_id)
        return None

    @staticmethod
    def create_media_from_copy(
            copy: models.ManualCopy,
            content: bytes,
    ) -> models.Media:
        if copy.id == 5:
            raise ValueError('test')

        return models.Media(
            owner_uuid=copy.owner_uuid,
            content=content,
        )
