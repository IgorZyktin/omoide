# -*- coding: utf-8 -*-
"""Routes related to item operations.
"""
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
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter(prefix='/items')


@router.get('/create')
@web.login_required
async def app_item_create(
        request: Request,
        parent_uuid: str = '',
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemCreateUseCase = Depends(
            dep.app_item_create_use_case),
        config: Config = Depends(dep.config),
        response_class: Response = HTMLResponse,
):
    """Create item page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)
    _parent_uuid = utils.cast_uuid(parent_uuid)

    result = await use_case.execute(policy, user, _parent_uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error, _parent_uuid)

    parent, permissions = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'url': request.url_for('search'),
        'parent': parent,
        'permissions': permissions,
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('item_create.html', context)


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
        'permissions': list(item.permissions or []),
    }


@router.get('/update/{uuid}')
@web.login_required
async def app_item_update(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemUpdateUseCase = Depends(
            dep.app_item_update_use_case),
        config: Config = Depends(dep.config),
        response_class: Response = HTMLResponse,
):
    """Edit item page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error, uuid)

    item, total, permissions = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'current_item': item,
        'item': item,
        'total': utils.sep_digits(total),
        'permissions': permissions,
        'url': request.url_for('search'),
        'query': infra.query_maker.QueryWrapper(query, details),
        'model': ujson.dumps(serialize_item(item), ensure_ascii=False),
        'initial_permissions': ujson.dumps([
            f'{x.uuid} {x.name}' for x in permissions
        ], ensure_ascii=False),
    }

    return dep.templates.TemplateResponse('item_update.html', context)


@router.get('/delete/{uuid}')
@web.login_required
async def app_item_delete(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemDeleteUseCase = Depends(
            dep.app_item_delete_use_case),
        config: Config = Depends(dep.config),
        response_class: Response = HTMLResponse,
):
    """Delete item page."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    result = await use_case.execute(policy, user, uuid)

    if isinstance(result, Failure):
        return web.redirect_from_error(request, result.error, uuid)

    item, total = result.value

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'current_item': item,
        'item': item,
        'url': request.url_for('search'),
        'uuid': uuid,
        'total': utils.sep_digits(total),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('item_delete.html', context)
