# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from starlette.templating import Jinja2Templates

from omoide import domain, use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import utils
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
        'api_url': request.url_for('api_home'),
    }
    return dep.templates.TemplateResponse('basic.html', context)


@router.get('/api/home')
async def api_home(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.HomeUseCase = fastapi.Depends(
            dep.get_home_use_case
        ),
):
    """Return portion of items for home directory."""
    aim = domain.aim_from_params(dict(request.query_params))
    items = await use_case.execute(user, aim)
    return utils.to_simple_items(request, items)
