# -*- coding: utf-8 -*-
"""User profile related routes.
"""
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from starlette import status

from omoide import domain
from omoide import use_cases
from omoide import utils
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/profile')
async def app_profile(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        use_case: use_cases.AppProfileUseCase = Depends(
            dep.profile_use_case),
        response_class: Type[Response] = HTMLResponse,
):
    """Show user home page."""
    if user.is_anon():
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    _result = await use_case.execute(user)

    if isinstance(_result, Failure):
        return web.redirect_from_error(request, _result.error)

    items_size, total_items = _result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'items_size': items_size,
        'total_items': total_items,
        'byte_count_to_text': utils.byte_count_to_text,
        'sep_digits': utils.sep_digits,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }

    return dep.templates.TemplateResponse('profile.html', context)
