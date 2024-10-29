"""Routes for item-related pages."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
import ujson

from omoide import custom_logging
from omoide import dependencies as dep
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_app.items import item_use_cases
from omoide.presentation import web
from omoide.presentation.app_config import Config

LOG = custom_logging.get_logger(__name__)

app_items_router = fastapi.APIRouter()


@app_items_router.get('/create/{parent_uuid}')
async def app_create_item(
    request: Request,
    parent_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Create item page."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = item_use_cases.AppCreateItemUseCase(mediator)

    try:
        parent, users_with_permission = await use_case.execute(
            user=user,
            parent_uuid=parent_uuid,
        )
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'endpoint': request.url_for('api_create_item'),
        'current_item': parent,
        'parent_item': parent,
        'users_with_permission': users_with_permission,
    }

    return templates.TemplateResponse('create_item.html', context)


def serialize_item(
    item: models.Item,
) -> dict[str, int | str | None | list[str]]:
    """Convert item to a simplified JSON form."""
    return {
        'uuid': str(item.uuid),
        'parent_uuid': str(item.parent_uuid) if item.parent_uuid else '',
        'name': item.name,
        'is_collection': item.is_collection,
        'content_ext': item.content_ext or '',
        'preview_ext': item.preview_ext or '',
        'thumbnail_ext': item.thumbnail_ext or '',
        'tags': item.tags,
        'permissions': [str(x) for x in item.permissions],
    }


@app_items_router.get('/update/{item_uuid}')
async def app_update_item(
    request: Request,
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Edit item page."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = item_use_cases.AppUpdateItemUseCase(mediator)

    try:
        (
            item,
            total,
            permissions,
            computed_tags,
            metainfo,
        ) = await use_case.execute(
            user=user,
            item_uuid=item_uuid,
        )
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    lower_tags = [tag.lower() for tag in item.tags]
    external_tags = [
        tag for tag in computed_tags if tag not in lower_tags and not utils.is_valid_uuid(tag)
    ]

    model = serialize_item(item)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': item,
        'item': item,
        'metainfo': metainfo,
        'total': utils.sep_digits(total),
        'permissions': permissions,
        'external_tags': external_tags,
        'url': request.url_for('app_search'),
        'model': ujson.dumps(model, ensure_ascii=False),
        'initial_permissions': ujson.dumps(
            [f'{x.uuid} {x.name}' for x in permissions], ensure_ascii=False
        ),
    }

    return templates.TemplateResponse('item_update.html', context)


@app_items_router.get('/delete/{item_uuid}')
async def app_delete_item(
    request: Request,
    item_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
):
    """Delete item page."""
    if user.is_anon:
        return RedirectResponse(request.url_for('app_forbidden'))

    use_case = item_use_cases.AppDeleteItemUseCase(mediator)

    try:
        item, total = await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.redirect_from_exc(request, exc)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': item,
        'item': item,
        'url': request.url_for('app_search'),
        'uuid': item_uuid,
        'total': utils.sep_digits(total),
    }

    return templates.TemplateResponse('item_delete.html', context)
