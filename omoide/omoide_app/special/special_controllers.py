"""Special pages for error descriptions."""

from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

app_special_router = fastapi.APIRouter()


@app_special_router.get(
    '/not_found',
    status_code=status.HTTP_404_NOT_FOUND,
)
async def app_not_found(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show <not found> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse('special_not_found.html', context)


@app_special_router.get(
    '/forbidden',
    status_code=status.HTTP_403_FORBIDDEN,
)
async def app_forbidden(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show <forbidden> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse('special_forbidden.html', context)


@app_special_router.get(
    '/bad_request',
    status_code=status.HTTP_400_BAD_REQUEST,
)
async def app_bad_request(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Show <bad request> page."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
    }
    return templates.TemplateResponse('special_bad_request.html', context)
