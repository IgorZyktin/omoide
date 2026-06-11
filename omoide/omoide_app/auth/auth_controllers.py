"""Auth related routes."""

import asyncio
from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import dependencies as dep
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.infra import interfaces as infra_interfaces
from omoide.omoide_app.auth import auth_use_cases
from omoide.presentation import web

app_auth_router = fastapi.APIRouter()
security = HTTPBasic(realm='omoide')


@app_auth_router.get('/login', response_model=None)
async def app_login(  # noqa: PLR0913
    request: Request,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    user: models.User = Depends(dep.get_current_user),
    authenticator: infra_interfaces.AbsAuthenticator = Depends(dep.get_authenticator),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    config: cfg.Config = Depends(dep.get_config),
    response_class: type[Response] = RedirectResponse,  # noqa: ARG001
) -> RedirectResponse:
    """Ask user for login and password."""
    url = request.url_for('app_home')

    if user.is_not_anon:
        return RedirectResponse(url)

    use_case = auth_use_cases.LoginUserUseCase(authenticator, database, users_repo)

    new_user = await use_case.execute(
        login=credentials.username,
        password=credentials.password,
    )

    if new_user.is_anon:
        await asyncio.sleep(config.penalty_wrong_password)
        raise fastapi.HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect login or password',
            headers={'WWW-Authenticate': 'Basic realm="omoide"'},
        )

    return RedirectResponse(url)


@app_auth_router.get('/logout')
async def app_logout(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
) -> HTMLResponse:
    """Clear authorization."""
    context = {
        'request': request,
        'config': config,
        'user': models.User.new_anon(),
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }
    return templates.TemplateResponse(
        request,
        name='logout.html',
        context=context,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )
