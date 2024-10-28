"""Browse related routes."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.browse import browse_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

LOG = custom_logging.get_logger(__name__)

app_browse_router = fastapi.APIRouter(prefix='/browse')


@app_browse_router.get('/{item_uuid}')
async def app_browse(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Browse contents of a single item."""
    if not aim_wrapper.aim.paged:
        use_case_dynamic = browse_use_cases.AppBrowseDynamicUseCase(mediator)

        try:
            parents, item, metainfo = await use_case_dynamic.execute(
                user=user,
                item_uuid=item_uuid,
            )
        except Exception as exc:
            return web.redirect_from_exc(request, exc)

        context = {
            'request': request,
            'config': config,
            'user': user,
            'aim_wrapper': aim_wrapper,
            'endpoint': request.url_for('api_browse', item_uuid=item_uuid),
            'parents': parents,
            'current_item': item,
            'metainfo': metainfo,
        }

        return templates.TemplateResponse('browse_dynamic.html', context)

    use_case_paged = browse_use_cases.AppBrowsePagedUseCase(mediator)

    try:
        result = await use_case_paged.execute(
            user=user,
            item_uuid=item_uuid,
            aim=aim_wrapper.aim,
        )
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    paginator = infra.Paginator(
        page=aim_wrapper.aim.page,
        items_per_page=aim_wrapper.aim.items_per_page,
        total_items=result.total_items,
        pages_in_block=const.PAGES_IN_ALBUM_AT_ONCE,
    )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'names': result.names,
        'aim_wrapper': aim_wrapper,
        'endpoint': request.url_for('api_browse', item_uuid=item_uuid),
        'result': result,
        'current_item': result.item,
        'parents': result.parents,
        'metainfo': result.metainfo,
        'paginator': paginator,
        'block_collections': True,
    }

    return templates.TemplateResponse('browse_paged.html', context)
