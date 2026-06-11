"""Routes related to item preview."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import cfg
from omoide import const
from omoide import dependencies as dep
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.omoide_app.preview import preview_use_cases
from omoide.presentation import infra
from omoide.presentation import web

app_preview_router = fastapi.APIRouter()


@app_preview_router.get('/preview/{item_uuid}', response_model=None)
async def app_preview(  # noqa: PLR0913
    request: Request,
    item_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
) -> HTMLResponse:
    """Browse contents of a single item as one object."""
    use_case = preview_use_cases.AppPreviewUseCase(
        database, items_repo, users_repo, meta_repo, tags_repo
    )

    result = await use_case.execute(user, item_uuid)

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

    return templates.TemplateResponse(request, 'preview.html', context)
