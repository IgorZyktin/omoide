# -*- coding: utf-8 -*-
"""Routes related to item deletion.
"""
import fastapi
from fastapi import Depends, Request
from starlette import status
from starlette.responses import RedirectResponse

from omoide import domain, utils
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.config import config

router = fastapi.APIRouter()


@router.get('/items/delete/{uuid}')
async def delete_item(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
):
    """Delete item page."""
    if user.is_anon():  # TODO - move it to a separate decorator
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    if not utils.is_valid_uuid(uuid):
        return RedirectResponse(request.url_for('bad_request'))

    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'url': request.url_for('search'),
        'uuid': uuid,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('delete_item.html', context)
