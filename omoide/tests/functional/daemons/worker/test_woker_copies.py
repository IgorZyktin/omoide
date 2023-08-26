# -*- coding: utf-8 -*-
"""Tests.
"""
from sqlalchemy.orm import Session

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

    def _create_copy(_session: Session, media: models.Media) -> int:
        _session.add(media)
        _session.flush()
        return media.id

    with database.start_session() as session:
        # this one is expected to be selected
        new_id = _create_copy(
            session,
            models.ManualCopy(
                created_at=utils.now(),
                processed_at=None,
                status='init',
                error='',
                owner_uuid=user.uuid,
                source_uuid=item.uuid,
                target_uuid=item.uuid,
                ext='jpg',
                target_folder='thumbnail',
            )
        )
        ids.append(new_id)

        # this one is expected to be skipped
        new_id = _create_copy(
            session,
            models.ManualCopy(
                created_at=utils.now(),
                processed_at=None,
                status='fail',
                error='',
                owner_uuid=user.uuid,
                source_uuid=item.uuid,
                target_uuid=item.uuid,
                ext='jpg',
                target_folder='thumbnail',
            )
        )
        ids.append(new_id)

        # this one is expected to be selected
        new_id = _create_copy(
            session,
            models.ManualCopy(
                created_at=utils.now(),
                processed_at=None,
                status='init',
                error='',
                owner_uuid=user.uuid,
                source_uuid=item.uuid,
                target_uuid=item.uuid,
                ext='jpg',
                target_folder='thumbnail',
            )
        )
        ids.append(new_id)

        # this one is expected to be skipped
        new_id = _create_copy(
            session,
            models.ManualCopy(
                created_at=utils.now(),
                processed_at=None,
                status='fail',
                error='',
                owner_uuid=user.uuid,
                source_uuid=item.uuid,
                target_uuid=item.uuid,
                ext='jpg',
                target_folder='thumbnail',
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
            models.ManualCopy
        ).filter(
            models.ManualCopy.id.in_(tuple(ids))  # noqa
        ).delete()
        session.commit()


def _do_testing(
        database: Database,
        ids: list[int],
) -> None:
    """Perform test."""
    selected_1, skipped_1, selected_2, skipped_2 = ids

    valid_ids = database.get_manual_copy_targets(
        limit=10,
    )

    assert len(valid_ids) == 2

    with database.start_session() as session:
        copy_1 = database.select_copy_operation(session, selected_1)

        if copy_1 is not None:
            media_1 = database.create_media_from_copy(copy_1, b'test')
            copy_1.status = 'done'
            session.add(media_1)
            session.flush()
            session.commit()
            assert media_1.id is not None

    dropped = database.drop_thumbnail_copies()
    assert dropped == 1

    dropped = database.drop_media(formula={})
    assert dropped == 1


def test_worker_copy_life_cycle(
        worker_database,
        db_test_user,
        db_test_item,
):
    """Must ensure that copy gets selected and deleted."""
    ids = _fill_database(worker_database, db_test_user, db_test_item)

    try:
        _do_testing(worker_database, ids)
    finally:
        _drop_resources(worker_database, ids)
