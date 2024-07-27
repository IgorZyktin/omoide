"""Search related operations."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from starlette.templating import Jinja2Templates

from omoide import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

app_search_router = APIRouter(prefix='/search')


@app_search_router.get('')
async def app_search(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
):
    """Main page of the application."""
    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_search'),
        'total_endpoint': request.url_for('api_search_total'),
    }
    return templates.TemplateResponse('search.html', context)
