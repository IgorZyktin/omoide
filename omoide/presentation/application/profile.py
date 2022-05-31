# -*- coding: utf-8 -*-
"""User profile related routes.
"""
import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette import status

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/profile')
async def profile(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Show user home page."""
    if user.is_anon():
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

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'url': request.url_for('search'),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('profile.html', context)
