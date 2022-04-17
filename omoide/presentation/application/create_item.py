# -*- coding: utf-8 -*-
"""Routes related to item creation.
"""
import fastapi
from fastapi import Depends
from starlette import status

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/create_item')
async def create_item(
        request: fastapi.Request,
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

    context = {
        'request': request,
        'config': config,
        'user': user,
        'url': request.url_for('search'),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('create_item.html', context)
