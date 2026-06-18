"""Routes for item-related pages."""

from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
import python_utilz as pu
import ujson

from omoide import cfg
from omoide import custom_logging
from omoide import dependencies as dep
from omoide import exceptions
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.omoide_app.items import item_use_cases
from omoide.presentation import web

LOG = custom_logging.get_logger(__name__)

app_items_router = fastapi.APIRouter()


@app_items_router.get('/create/{parent_uuid}', response_model=None)
async def app_create_item(  # noqa: PLR0913
    request: Request,
    parent_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
) -> HTMLResponse:
    """Create item page."""
    if user.is_anon:
        msg = 'Anonymous users are not allowed to create items'
        raise exceptions.AccessDeniedError(msg)

    use_case = item_use_cases.AppCreateItemUseCase(database, items_repo, users_repo)

    result = await use_case.execute(
        user=user,
        parent_uuid=parent_uuid,
    )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': request.url_for('app_search'),
        'endpoint': request.url_for('api_create_item'),
        'current_item': result.parent,
        'parent_item': result.parent,
        'users_with_permission': result.users_with_permission,
    }

    return templates.TemplateResponse(request, 'create_item.html', context)


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
        'tags': list(item.tags),
        'permissions': [str(x) for x in item.permissions],
    }


@app_items_router.get('/update/{item_uuid}', response_model=None)
async def app_update_item(  # noqa: PLR0913
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
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
) -> HTMLResponse:
    """Edit item page."""
    if user.is_anon:
        msg = 'Anonymous users are not allowed to update items'
        raise exceptions.AccessDeniedError(msg)

    use_case = item_use_cases.AppUpdateItemUseCase(database, items_repo, users_repo, meta_repo)

    result = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
    )

    lower_tags = [tag.lower() for tag in result.item.tags]
    external_tags = [
        tag for tag in result.computed_tags if tag not in lower_tags and not pu.is_valid_uuid(tag)
    ]

    model = serialize_item(result.item)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': result.item,
        'item': result.item,
        'metainfo': result.metainfo,
        'notes': result.notes,
        'total': pu.sep_digits(result.total),
        'permissions': result.can_see,
        'external_tags': external_tags,
        'url': request.url_for('app_search'),
        'model': ujson.dumps(model, ensure_ascii=False),
        'initial_permissions': ujson.dumps(
            [f'{x.uuid} {x.name}' for x in result.can_see], ensure_ascii=False
        ),
    }

    return templates.TemplateResponse(request, 'item_update.html', context)


@app_items_router.get('/delete/{item_uuid}', response_model=None)
async def app_delete_item(  # noqa: PLR0913
    request: Request,
    item_uuid: UUID,
    templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
    config: Annotated[cfg.Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    response_class: type[Response] = HTMLResponse,  # noqa: ARG001
) -> HTMLResponse:
    """Delete item page."""
    if user.is_anon:
        msg = 'Anonymous users are not allowed to delete items'
        raise exceptions.AccessDeniedError(msg)

    use_case = item_use_cases.AppDeleteItemUseCase(database, items_repo)

    result = await use_case.execute(user, item_uuid)

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': result.item,
        'item': result.item,
        'url': request.url_for('app_search'),
        'uuid': item_uuid,
        'total': pu.sep_digits(result.total),
    }

    return templates.TemplateResponse(request, 'item_delete.html', context)
