"""Hope page related routes."""

from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import dependencies as dep
from omoide import models
from omoide.presentation import web

app_home_router = fastapi.APIRouter()


@app_home_router.get('/')
async def app_home(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Home endpoint for user."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_paginated': True,
        'block_direct': False,
        'endpoint': request.url_for('api_home'),
    }
    return templates.TemplateResponse('home.html', context)
