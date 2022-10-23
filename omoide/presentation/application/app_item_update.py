# -*- coding: utf-8 -*-
"""Routes related to media edit.
"""
from uuid import UUID

import fastapi
import ujson
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse

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

router = fastapi.APIRouter(prefix='/items/update')


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


@router.get('/{uuid}')
async def app_item_edit(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemUpdateUseCase = Depends(
            dep.app_item_update_use_case),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
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
