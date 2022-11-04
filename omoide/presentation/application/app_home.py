# -*- coding: utf-8 -*-
"""Hope page related routes.
"""
import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/')
async def app_home(
        request: Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        config: Config = Depends(dep.config),
        response_class: Response = HTMLResponse,
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
