# -*- coding: utf-8 -*-
"""Routes related to item creation.
"""
import fastapi
from fastapi import Depends, Request
from starlette import status

from omoide import domain, utils
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/items/create')
async def create_item(
        request: Request,
        parent_uuid: str = '',
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
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

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    if not utils.is_valid_uuid(parent_uuid):
        parent_uuid = ''

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'url': request.url_for('search'),
        'parent_uuid': parent_uuid,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('create_item.html', context)
