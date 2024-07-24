"""Browse related routes."""
import http
from typing import Annotated
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/not_found')
async def not_found(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show <not found> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse(
        name='exc_not_found.html',
        context=context,
        status_code=http.HTTPStatus.NOT_FOUND,
    )


@router.get('/unauthorized')
async def unauthorized(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show <unauthorized> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse(
        name='exc_unauthorized.html',
        context=context,
    )


@router.get('/forbidden')
async def forbidden(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show <forbidden> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse(
        name='exc_forbidden.html',
        context=context,
        status_code=http.HTTPStatus.FORBIDDEN,
    )


@router.get('/bad_request')
async def bad_request(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Show <bad request> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse(
        name='exc_bad_request.html',
        context=context,
        status_code=http.HTTPStatus.BAD_REQUEST,
    )
