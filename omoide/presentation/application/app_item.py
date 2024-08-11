"""Routes related to item operations."""
from typing import Annotated
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from starlette.responses import Response
import ujson

from omoide import domain
from omoide import interfaces
from omoide import models
from omoide import use_cases
from omoide import utils
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter(prefix='/items')


def serialize_item(
        item: domain.Item,
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


@router.get('/update/{uuid}')
async def app_item_update(
        request: Request,
        uuid: UUID,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemUpdateUseCase = Depends(
            dep.app_item_update_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: type[Response] = HTMLResponse,
):
    """Edit item page."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error, uuid)

    item, total, permissions, computed_tags, metainfo = result.value

    lower_tags = [tag.lower() for tag in item.tags]
    external_tags = [
        tag for tag in computed_tags
        if tag not in lower_tags and not utils.is_valid_uuid(tag)
    ]

    model = serialize_item(item)
    thumbnail_origin = ''
    if metainfo:
        copied_image_from = metainfo.extras.get('copied_image_from')
        if copied_image_from:
            thumbnail_origin = copied_image_from

    model['copied_image_from'] = thumbnail_origin or str(item.uuid)

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
        'initial_permissions': ujson.dumps([
            f'{x.uuid} {x.name}' for x in permissions
        ], ensure_ascii=False),
    }

    return templates.TemplateResponse('item_update.html', context)


@router.get('/delete/{uuid}')
async def app_item_delete(
        request: Request,
        uuid: UUID,
        templates: Annotated[Jinja2Templates, Depends(dep.get_templates)],
        user: models.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemDeleteUseCase = Depends(
            dep.app_item_delete_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        response_class: type[Response] = HTMLResponse,
):
    """Delete item page."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error, uuid)

    item, total = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': item,
        'item': item,
        'url': request.url_for('app_search'),
        'uuid': uuid,
        'total': utils.sep_digits(total),
    }

    return templates.TemplateResponse('item_delete.html', context)
