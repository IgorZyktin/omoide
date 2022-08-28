# -*- coding: utf-8 -*-
"""Item related API operations.
"""
import http
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response

from omoide import domain
from omoide import use_cases
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import api_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/items')


@router.post(
    '',
    status_code=http.HTTPStatus.CREATED,
    response_model=api_models.OnlyUUID,
)
async def api_create_item(
        request: Request,
        response: Response,
        payload: api_models.CreateItemIn,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.CreateItemUseCase = Depends(
            dep.create_item_use_case),
):
    """Create item."""
    result = await use_case.execute(policy, user, payload)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    response.headers['Location'] = request.url_for('api_read_item',
                                                   uuid=result.value)

    return api_models.OnlyUUID(uuid=result.value)


@router.get('/{uuid}')
async def api_read_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.ReadItemUseCase = Depends(
            dep.read_item_use_case),
):
    """Get item."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return result.value


@router.patch('/{uuid}')
async def api_partial_update_item(
        uuid: UUID,
        operations: list[api_models.PatchOperation],
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.UpdateItemUseCase = Depends(
            dep.update_item_use_case),
):
    """Update item."""
    result = await use_case.execute(policy, user, uuid, operations)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return {'result': 'ok'}


@router.delete(
    '/{uuid}',
    response_model=api_models.OnlyUUID,
)
async def api_delete_item(
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.DeleteItemUseCase = Depends(
            dep.delete_item_use_case),
):
    """Delete item.

    If item does not exist return 404.

    If item was successfully deleted, return UUID of the parent
    (so you could browse which items are still exist in this collection).
    """
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    return api_models.OnlyUUID(uuid=result.value)
