"""Hope page related routes."""
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


@router.get('/')
async def app_home(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = fastapi.Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: Type[Response] = HTMLResponse,
):
    """Home endpoint for user."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_paginated': True,
        'api_url': request.url_for('api_home'),
    }
    return templates.TemplateResponse('home.html', context)
