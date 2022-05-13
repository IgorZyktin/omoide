# -*- coding: utf-8 -*-
"""Browse related routes.
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
    }
    return dep.templates.TemplateResponse('basic.html', context)
