# -*- coding: utf-8 -*-
"""Auth related routes.
"""
import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from starlette import status

from omoide import domain
from omoide import use_cases
from omoide.domain import interfaces
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()
security = HTTPBasic(realm='omoide')


@router.get('/login')
async def login(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        credentials: HTTPBasicCredentials = Depends(security),
        authenticator: interfaces.AbsAuthenticator = Depends(
            dep.get_authenticator),
        use_case: use_cases.AuthUseCase = Depends(dep.get_auth_use_case),
        response_class=RedirectResponse,
):
    """Ask user for login and password."""
    url = request.url_for('search')

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
async def logout(
        request: Request,
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Clear authorization."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': domain.User.new_anon(),
        'aim': aim,
        'url': request.url_for('search'),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse(
        name='logout.html',
        context=context,
        status_code=401,
    )
