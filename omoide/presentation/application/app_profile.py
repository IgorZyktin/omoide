"""User profile related routes."""
from typing import Annotated
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import models
from omoide.domain import errors
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/profile')
async def app_profile(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: models.User = Depends(dep.get_current_user),
    config: Config = Depends(dep.get_config),
    aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
    response_class: Type[Response] = HTMLResponse,
):
    """Show user home page."""
    if user.is_anon or user.uuid is None:
        error = errors.AuthenticationRequired()
        return web.redirect_from_error(request, error)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
    }
    return templates.TemplateResponse('profile.html', context)


@router.get('/profile/new')
async def app_profile_new(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: models.User = Depends(dep.get_current_user),
    config: Config = Depends(dep.get_config),
    aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
    response_class: Type[Response] = HTMLResponse,
):
    """Show recent updates."""
    if user.is_anon or user.uuid is None:
        error = errors.AuthenticationRequired()
        return web.redirect_from_error(request, error)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_get_recent_updates'),
    }
    return templates.TemplateResponse('profile_new.html', context)
