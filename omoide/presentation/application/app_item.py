# -*- coding: utf-8 -*-
"""Routes related to item operations.
"""
from typing import Type
from uuid import UUID

import fastapi
import ujson
from fastapi import Depends
from fastapi import Request
from starlette.responses import HTMLResponse
from starlette.responses import Response

from omoide import domain
from omoide import use_cases
from omoide import utils
from omoide.domain import interfaces
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter(prefix='/items')


@router.get('/create/{uuid}')
async def app_item_create(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemCreateUseCase = Depends(
            dep.app_item_create_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = HTMLResponse,
):
    """Create item page."""
    valid_uuid = utils.cast_uuid(uuid)

    result = await use_case.execute(policy, user, valid_uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(
            templates, request, result.error, valid_uuid)

    parent, permissions = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'url': templates.url_for(request, 'app_search'),
        'parent': parent,
        'permissions': permissions,
        'locate': web.get_locator(templates, request, config.prefix_size),
    }

    return templates.TemplateResponse('item_create.html', context)


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
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemUpdateUseCase = Depends(
            dep.app_item_update_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = HTMLResponse,
):
    """Edit item page."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(
            templates, request, result.error, uuid)

    item, total, permissions, computed_tags = result.value

    lower_tags = [tag.lower() for tag in item.tags]
    external_tags = [
        tag for tag in computed_tags
        if tag not in lower_tags and not utils.is_valid_uuid(tag)
    ]

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': item,
        'item': item,
        'total': utils.sep_digits(total),
        'permissions': permissions,
        'external_tags': external_tags,
        'url': templates.url_for(request, 'app_search'),
        'model': ujson.dumps(serialize_item(item), ensure_ascii=False),
        'initial_permissions': ujson.dumps([
            f'{x.uuid} {x.name}' for x in permissions
        ], ensure_ascii=False),
    }

    return templates.TemplateResponse('item_update.html', context)


@router.get('/delete/{uuid}')
async def app_item_delete(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemDeleteUseCase = Depends(
            dep.app_item_delete_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = HTMLResponse,
):
    """Delete item page."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(templates, request, result.error, uuid)

    item, total = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim_wrapper': aim_wrapper,
        'current_item': item,
        'item': item,
        'url': templates.url_for(request, 'app_search'),
        'uuid': uuid,
        'total': utils.sep_digits(total),
    }

    return templates.TemplateResponse('item_delete.html', context)


@router.get('/download/{uuid}')
async def app_items_download(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemsDownloadUseCase = Depends(
            dep.app_items_download_use_case),
        config: Config = Depends(dep.get_config),
        templates: web.TemplateEngine = Depends(dep.get_templates),
        response_class: Type[Response] = HTMLResponse,
):
    """Return links of children to download them."""
    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(templates, request, result.error, uuid)

    numerated_items = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'uuid': uuid,
        'numerated_items': numerated_items,
        'locate': web.get_locator(templates, request, config.prefix_size),
    }

    return templates.TemplateResponse('items_download.html', context)
