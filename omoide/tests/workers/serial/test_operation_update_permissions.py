"""Test."""

from uuid import UUID
from uuid import uuid4

import pytest

from omoide import const
from omoide import models
from omoide import serial_operations as so
from omoide.workers.serial import operations as op
from omoide.workers.serial.worker import SerialWorker


@pytest.mark.asyncio
async def test_serial_operation_update_permissions(
    serial_worker: SerialWorker,
):
    # arrange
    worker = serial_worker

    user_common = {
        'role': models.Role.USER,
        'is_public': False,
    }

    user_1 = models.User(
        id=1, login='l1', uuid=uuid4(), name='user_1', **user_common
    )
    user_2 = models.User(
        id=2, login='l2', uuid=uuid4(), name='user_2', **user_common
    )
    user_3 = models.User(
        id=3, login='l3', uuid=uuid4(), name='user_3', **user_common
    )
    users = [user_1, user_2, user_3]

    items_common = {
        'owner_uuid': user_1.uuid,
        'number': 0,
        'is_collection': False,
        'content_ext': None,
        'preview_ext': None,
        'thumbnail_ext': None,
        'status': models.Status.AVAILABLE,
        'tags': [],
    }

    item_1 = models.Item(
        id=1, uuid=uuid4(), parent_uuid=None, name='item_1', **items_common
    )
    item_2 = models.Item(
        id=2,
        uuid=uuid4(),
        parent_uuid=item_1.uuid,
        name='item_2',
        **items_common,
    )
    item_3 = models.Item(
        id=3,
        uuid=uuid4(),
        parent_uuid=item_2.uuid,
        name='item_3',
        **items_common,
    )
    item_4 = models.Item(
        id=4,
        uuid=uuid4(),
        parent_uuid=item_3.uuid,
        name='item_4',
        **items_common,
    )
    item_5 = models.Item(
        id=5,
        uuid=uuid4(),
        parent_uuid=item_4.uuid,
        name='item_5',
        **items_common,
    )
    items = [item_1, item_2, item_3, item_4, item_5]

    item_1.permissions = [user_2.uuid, user_3.uuid]
    item_2.permissions = [user_2.uuid, user_3.uuid]
    item_3.permissions = [user_1.uuid, user_2.uuid]
    item_4.permissions = [user_1.uuid, user_2.uuid]
    item_5.permissions = [user_1.uuid, user_2.uuid]

    try:
        async with worker.mediator.database.transaction() as conn:
            for user in users:
                await worker.mediator.users.create(conn, user, '', 0)

            for item in items:
                await worker.mediator.items.create(conn, item)

        operation = so.SerialOperation.from_name(
            name='update_permissions',
            extras={
                'item_uuid': str(item_3.uuid),
                'added': [str(user_3.uuid)],
                'deleted': [str(user_2.uuid)],
                'original': [str(user_1.uuid), str(user_2.uuid)],
                'apply_to_parents': True,
                'apply_to_children': True,
                'apply_to_children_as': const.ApplyAs.DELTA,
            },
        )
        executor = op.SerialOperationExecutor.from_operation(
            operation=operation,
            config=worker.config,
            mediator=worker.mediator,
        )

        # act
        await executor.execute()

        # assert
        async with worker.mediator.database.transaction() as conn:
            item_1 = await worker.mediator.items.get_by_id(conn, item_1.id)
            item_2 = await worker.mediator.items.get_by_id(conn, item_2.id)
            item_3 = await worker.mediator.items.get_by_id(conn, item_3.id)
            item_4 = await worker.mediator.items.get_by_id(conn, item_4.id)
            item_5 = await worker.mediator.items.get_by_id(conn, item_5.id)

        def cast_to_readable(uuid: UUID) -> str:
            match uuid:
                case user_1.uuid:
                    return 'user_1'
                case user_2.uuid:
                    return 'user_2'
                case user_3.uuid:
                    return 'user_3'
                case _:
                    msg = f'Unknown UUID {uuid}'
                    raise RuntimeError(msg)

        assert {cast_to_readable(x) for x in item_1.permissions} == {'user_3'}
        assert {cast_to_readable(x) for x in item_2.permissions} == {'user_3'}

        # NOTE - modification target is expected
        # to be updated before operation call
        assert {cast_to_readable(x) for x in item_3.permissions} == {
            'user_1',
            'user_2',
        }

        assert {cast_to_readable(x) for x in item_4.permissions} == {
            'user_1',
            'user_3',
        }
        assert {cast_to_readable(x) for x in item_5.permissions} == {
            'user_1',
            'user_3',
        }
    finally:
        async with worker.mediator.database.transaction() as conn:
            for user in users:
                await worker.mediator.users.delete(conn, user)

            for item in items:
                await worker.mediator.items.delete(conn, item)
