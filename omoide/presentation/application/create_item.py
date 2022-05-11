# -*- coding: utf-8 -*-
"""Routes related to item creation.
"""
import fastapi
from fastapi import Depends, Request, Response
from starlette import status

from omoide import domain, use_cases, utils
from omoide.domain.crud import CreateItemPayload
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/create_item')
async def create_item(
        request: Request,
        parent_uuid: str = '',
        user: domain.User = Depends(dep.get_current_user),
):
    """Create item page."""
    if user.is_anon():  # TODO - move it to a separate decorator
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    if not utils.is_valid_uuid(parent_uuid):
        parent_uuid = ''

    context = {
        'request': request,
        'config': config,
        'user': user,
        'url': request.url_for('search'),
        'parent_uuid': parent_uuid,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('create_item.html', context)


@router.post('/api/create_item')
async def api_create_item(
        request: Request,
        response: Response,
        payload: CreateItemPayload,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.CreateItemUseCase = Depends(
            dep.get_create_item_use_case
        ),
):
    """Try creating new item."""
    if user.is_anon():  # TODO - move it to a separate decorator
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    # TODO - refactor this
    if payload.parent_uuid and len(payload.parent_uuid) != 36:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Seems like parent UUID is invalid',
        )

    if len(payload.item_name) > 60:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Please use shorter name',
        )

    if payload.is_collection and not payload.item_name:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='You have to specify name for collection',
        )

    if len(payload.tags) > 100:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Too many tags',
        )

    if len(payload.permissions) > 100:
        raise fastapi.HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Too many permissions',
        )

    for tag in payload.tags:
        if len(tag) > 64:
            raise fastapi.HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Tag is too long',
            )

    for user_uuid in payload.permissions:
        if len(user_uuid) != 36:
            raise fastapi.HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Incorrect user uuid: {user_uuid!r}',
            )

    access, item_uuid = await use_case.execute(user, payload)

    if access.does_not_exist or access.is_not_given:
        raise fastapi.HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Parent with this UUID does not exist',
        )

    if payload.go_upload:
        url = request.url_for('upload') + f'?parent_uuid={item_uuid}'
    else:
        url = request.url_for('preview', uuid=item_uuid)

    return {'url': url}
