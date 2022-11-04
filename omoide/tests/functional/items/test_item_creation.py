# -*- coding: utf-8 -*-
"""Tests.
"""
from omoide import use_cases
from omoide.infra.special_types import Success


async def test_item_creation(
        database,
        items_write_repository,
        metainfo_repository,
        policy,
        user,
        raw_item_in,
):
    """Test that item gets created."""
    # arrange
    use_case = use_cases.ApiItemCreateUseCase(items_write_repository,
                                              metainfo_repository)

    # act
    uuid = await use_case.execute(
        policy=policy,
        user=user,
        payload=raw_item_in,
    )

    # assert
    try:
        assert isinstance(uuid, Success)
        assert uuid.value is not None
    finally:
        database.execute(
            'DELETE FROM items WHERE uuid = :uuid',
            {'uuid': str(uuid)},
        )
