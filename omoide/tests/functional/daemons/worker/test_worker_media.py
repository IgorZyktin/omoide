# -*- coding: utf-8 -*-
"""Tests.
"""
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from omoide import utils
from omoide.daemons.worker.database import Database
from omoide.storage.database import models


def _fill_database(
        database: Database,
        user: models.User,
        item: models.Item,
) -> list[int]:
    """Create required test objects."""
    ids: list[int] = []

    def _create_media(_session: Session, media: models.Media) -> int:
        _session.add(media)
        _session.flush()
        return media.id

    with database.start_session() as session:
        # this one is expected to be selected
        new_id = _create_media(
            session,
            models.Media(
                owner_uuid=user.uuid,
                item_uuid=item.uuid,
                target_folder='thumbnail',
                created_at=utils.now(),
                processed_at=None,
                content=b'test-1',
                ext='jpg',
                replication={},
                error='',
                attempts=0,
            )
        )
        ids.append(new_id)

        # this one is expected to be skipped
        new_id = _create_media(
            session,
            models.Media(
                owner_uuid=user.uuid,
                item_uuid=item.uuid,
                target_folder='thumbnail',
                created_at=utils.now(),
                processed_at=None,
                content=b'test-2',
                ext='jpg',
                replication={'test-hot': True},
                error='',
                attempts=0,
            )
        )
        ids.append(new_id)

        # this one is expected to be selected
        new_id = _create_media(
            session,
            models.Media(
                owner_uuid=user.uuid,
                item_uuid=item.uuid,
                target_folder='thumbnail',
                created_at=utils.now(),
                processed_at=None,
                content=b'test-3',
                ext='jpg',
                replication={},
                error='',
                attempts=0,
            )
        )
        ids.append(new_id)

        # this one is expected to be skipped
        new_id = _create_media(
            session,
            models.Media(
                owner_uuid=user.uuid,
                item_uuid=item.uuid,
                target_folder='thumbnail',
                created_at=utils.now(),
                processed_at=None,
                content=b'test-4',
                ext='jpg',
                replication={},
                error='',
                attempts=25,
            )
        )
        ids.append(new_id)

        session.commit()

    return ids


def _drop_resources(
        database: Database,
        ids: list[int],
) -> None:
    """Drop created test objects."""
    with database.start_session() as session:
        session.query(
            models.Media
        ).filter(
            models.Media.id.in_(tuple(ids))  # noqa
        ).delete()
        session.commit()


def _do_testing(
        database: Database,
        ids: list[int],
) -> None:
    """Perform test."""
    selected_1, skipped_1, selected_2, skipped_2 = ids

    valid_ids = database.get_media_ids(
        formula={'test-hot': True},
        limit=10,
        max_attempts=5,
    )

    assert len(valid_ids) == 2

    with database.start_session() as session:
        media_1 = database.select_media(session, selected_1)
        media_1.replication = {'test-hot': True}
        flag_modified(media_1, 'replication')
        session.commit()

    dropped = database.drop_media(formula={'test-hot': True})
    assert dropped == 2


def test_worker_media_life_cycle(
        worker_database,
        db_test_user,
        db_test_item,
):
    """Must ensure that media gets selected and deleted."""
    ids = _fill_database(worker_database, db_test_user, db_test_item)

    try:
        _do_testing(worker_database, ids)
    finally:
        _drop_resources(worker_database, ids)
