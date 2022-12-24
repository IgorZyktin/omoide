# -*- coding: utf-8 -*-
"""Auth related routes.
"""
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from starlette import status

from omoide import domain
from omoide import use_cases
from omoide.domain import interfaces
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()
security = HTTPBasic(realm='omoide')


@router.get('/login')
async def app_login(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        credentials: HTTPBasicCredentials = Depends(security),
        authenticator: interfaces.AbsAuthenticator = Depends(
            dep.get_authenticator),
        use_case: use_cases.AuthUseCase = Depends(dep.get_auth_use_case),
        response_class: Type[Response] = HTMLResponse,
):
    """Ask user for login and password."""
    url = request.url_for('app_home')

    if not user.is_anon():
        # already logged in
        return RedirectResponse(url)

    new_user = await use_case.execute(credentials, authenticator)

    if new_user.is_anon():
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    return RedirectResponse(url)


@router.get('/logout')
async def app_logout(
        request: Request,
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Clear authorization."""
    context = {
        'request': request,
        'config': config,
        'user': domain.User.new_anon(),
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }
    return dep.get_templates().TemplateResponse(
        name='logout.html',
        context=context,
        status_code=401,
    )
