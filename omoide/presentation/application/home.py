# -*- coding: utf-8 -*-
"""Hope page related routes.
"""
import fastapi
from starlette.templating import Jinja2Templates

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation.config import config

router = fastapi.APIRouter()

templates = Jinja2Templates(directory='omoide/presentation/templates')


@router.get('/')
async def home(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
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
