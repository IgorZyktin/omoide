"""Browse related routes."""
from typing import Annotated
from typing import Type
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import interfaces
from omoide import models
from omoide import use_cases
from omoide.infra.special_types import Failure
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

app_browse_router = fastapi.APIRouter(prefix='/browse')


@app_browse_router.get('/{item_uuid}')
async def app_browse(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    item_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    policy: interfaces.AbsPolicy = Depends(dep.get_policy),
    use_case: use_cases.AppBrowseUseCase = Depends(
        dep.app_browse_use_case),
    config: Config = Depends(dep.get_config),
    aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
    response_class: Type[Response] = HTMLResponse,
):
    """Browse contents of a single item as collection."""
    aim = aim_wrapper.aim

    _result = await use_case.execute(policy, user, item_uuid, aim)

    if isinstance(_result, Failure):
        return web.redirect_from_error(request, _result.error, item_uuid)

    result = _result.value

    names = result.names

    context = {
        'request': request,
        'config': config,
        'user': user,
        'uuid': item_uuid,
        'names': names,
        'aim_wrapper': aim_wrapper,
        'location': result.location,
        'endpoint': request.url_for('api_browse', item_uuid=item_uuid),
        'result': result,
        'current_item': result.item,
        'metainfo': result.metainfo,
    }

    if result.paginated:
        template = 'browse_paginated.html'
        paginator = infra.Paginator(
            page=aim.page,
            items_per_page=aim.items_per_page,
            total_items=result.total_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )
        context['paginator'] = paginator
        context['block_collections'] = True
    else:
        template = 'browse_dynamic.html'

    return templates.TemplateResponse(template, context)
