# -*- coding: utf-8 -*-
"""Hope page related routes.
"""
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response

from omoide import domain
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/')
async def app_home(
        request: Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = HTMLResponse,
):
    """Home endpoint for user."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_paginated': True,
        'api_url': templates.url_for(request, 'api_home'),
    }
    return templates.TemplateResponse('home.html', context)
