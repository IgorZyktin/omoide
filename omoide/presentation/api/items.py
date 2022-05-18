# -*- coding: utf-8 -*-
"""Item related API operations.
"""
import http
from uuid import UUID

import fastapi
from fastapi import HTTPException

from omoide import domain, use_cases
from omoide.domain import exceptions
from omoide.presentation import dependencies as dep

router = fastapi.APIRouter(prefix='/api/items')


@router.get('/{uuid}')
async def get_item(
        uuid: UUID,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.GetItemUseCase = fastapi.Depends(
            dep.get_item_use_case),
):
    """Get item."""
    try:
        item = await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
    return item.dict()


@router.delete('/{uuid}', status_code=http.HTTPStatus.NO_CONTENT)
async def delete_item(
        uuid: UUID,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.DeleteItemUseCase = fastapi.Depends(
            dep.delete_item_use_case),
):
    """Delete item."""
    try:
        await use_case.execute(user, uuid)
    except exceptions.NotFound as exc:
        raise HTTPException(status_code=http.HTTPStatus.NOT_FOUND,
                            detail=str(exc))
    except exceptions.Forbidden as exc:
        raise HTTPException(status_code=http.HTTPStatus.FORBIDDEN,
                            detail=str(exc))
