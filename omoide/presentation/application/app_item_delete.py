# -*- coding: utf-8 -*-
"""Routes related to item deletion.
"""
from uuid import UUID

import fastapi
from fastapi import Depends
from fastapi import Request

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

router = fastapi.APIRouter(prefix='/items/delete')


@router.get('{uuid}')
async def app_item_delete(
        request: Request,
        uuid: UUID,
        user: domain.User = Depends(dep.get_current_user),
        policy: interfaces.AbsPolicy = Depends(dep.get_policy),
        use_case: use_cases.AppItemDeleteUseCase = Depends(
            dep.app_item_delete_use_case),
        config: Config = Depends(dep.config),
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
        'item': item,
        'url': request.url_for('search'),
        'uuid': uuid,
        'total': utils.sep_digits(total),
        'query': infra.query_maker.QueryWrapper(query, details),
    }

    return dep.templates.TemplateResponse('item_delete.html', context)
