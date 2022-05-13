# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from starlette.templating import Jinja2Templates

from omoide import domain, use_cases
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


@router.get('/api/home')
async def api_home(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.HomeUseCase = fastapi.Depends(
            dep.get_home_use_case
        ),
):
    """Return portion of items for home directory."""
    items = await use_case.execute(user)
    simple_items = []

    for item in items:
        if item.is_collection:
            href = request.url_for('browse', uuid=item.uuid)
        else:
            href = request.url_for('preview', uuid=item.uuid)

        if item.thumbnail_ext is None:
            thumbnail = request.url_for('static', path='empty.png')
        else:
            thumbnail = (
                f'/content/{item.owner_uuid}/thumbnail/{item.thumbnail_path}'
            )

        simple_item = {
            'uuid': item.uuid,
            'name': item.name,
            'is_collection': item.is_collection,
            'href': href,
            'thumbnail': thumbnail,
        }

        simple_items.append(simple_item)

    return simple_items
