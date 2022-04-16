# -*- coding: utf-8 -*-
"""Auth related routes.
"""

import fastapi
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette import status

from omoide import domain, use_cases
from omoide.domain import interfaces
from omoide.presentation import dependencies, infra, constants
from omoide.presentation.config import config

router = fastapi.APIRouter()
security = HTTPBasic(realm='omoide')


@router.get('/login')
async def login(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dependencies.get_current_user),
        credentials: HTTPBasicCredentials = fastapi.Depends(security),
        authenticator: interfaces.AbsAuthenticator = fastapi.Depends(
            dependencies.get_authenticator,
        ),
        use_case: use_cases.AuthUseCase = fastapi.Depends(
            dependencies.get_auth_use_case,
        ),
        response_class=fastapi.responses.RedirectResponse,
):
    """Ask user for login and password."""
    url = request.url_for('search')

    if not user.is_anon():
        # already logged in
        return fastapi.responses.RedirectResponse(url)

    new_user = await use_case.execute(credentials, authenticator)

    if new_user.is_anon():
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    return fastapi.responses.RedirectResponse(url)


@router.get('/logout')
async def logout(
        request: fastapi.Request,
        response_class=fastapi.responses.HTMLResponse,
):
    """Clear authorization."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)

    context = {
        'request': request,
        'config': config,
        'user': domain.User.new_anon(),
        'url': request.url_for('search'),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dependencies.templates.TemplateResponse(
        name='logout.html',
        context=context,
        status_code=401,
    )
