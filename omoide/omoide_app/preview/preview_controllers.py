"""Routes related to item preview."""

from typing import Annotated
from typing import Type
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import const
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.preview import preview_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

app_preview_router = fastapi.APIRouter()


@app_preview_router.get('/preview/{item_uuid}')
async def app_preview(
    request: Request,
    item_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: Type[Response] = HTMLResponse,
):
    """Browse contents of a single item as one object."""
    use_case = preview_use_cases.AppPreviewUseCase(mediator)

    try:
        result = await use_case.execute(user, item_uuid)
    except Exception as exc:
        web.redirect_from_exc(request, exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'current_item': result.item,
        'parents': result.parents,
        'metainfo': result.metainfo,
        'all_tags': sorted(result.all_tags),
        'album': infra.Album(
            sequence=result.siblings,
            position=result.item,
            items_on_page=const.PAGES_IN_ALBUM_AT_ONCE,
        ),
        'block_collections': True,
        'block_ordered': True,
        'block_direct': True,
        'block_paginated': True,
    }

    return templates.TemplateResponse('preview.html', context)
