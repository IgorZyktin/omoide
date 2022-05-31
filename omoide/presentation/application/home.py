# -*- coding: utf-8 -*-
"""Hope page related routes.
"""
import fastapi
from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='omoide/presentation/templates')


@router.get('/')
async def home(
        request: Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Home endpoint for user."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': domain.aim_from_params(dict(request.query_params)),
        'block_paginated': True,
        'api_url': request.url_for('api_home'),
    }
    return dep.templates.TemplateResponse('basic.html', context)
