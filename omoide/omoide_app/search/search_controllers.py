"""Search page."""
from typing import Annotated
from typing import Type

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from starlette.templating import Jinja2Templates

from omoide import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

app_search_router = APIRouter()


@app_search_router.get('/search')
async def app_search(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    response_class: Type[Response] = HTMLResponse,
):
    """Main page of the application."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_paginated': True,
        'block_direct': True,
        'endpoint': request.url_for('api_search'),
        'total_endpoint': request.url_for('api_search_total'),
    }
    return templates.TemplateResponse('search.html', context)


@app_search_router.get('/home')
async def app_home(
    request: Request,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: Type[Response] = HTMLResponse,
):
    """Home endpoint for user."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'block_paginated': True,
        'block_direct': True,
        'endpoint': request.url_for('api_home'),
    }
    return templates.TemplateResponse('home.html', context)
