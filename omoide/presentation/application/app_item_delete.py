# -*- coding: utf-8 -*-
"""Routes related to item deletion.
"""
import fastapi
from fastapi import Depends, Request
from starlette.responses import RedirectResponse

import omoide.use_cases.application.uc_app_items
from omoide import domain, utils, use_cases
from omoide.domain import exceptions
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/items/delete/{uuid}')
async def app_item_delete(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
        use_case: omoide.use_cases.application.uc_app_items.AppItemDeleteUseCase = Depends(
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

    try:
        total, item = await use_case.execute(user, uuid)
    except exceptions.IncorrectUUID:
        return RedirectResponse(request.url_for('bad_request'))
    except exceptions.NotFound:
        return RedirectResponse(request.url_for('not_found') + f'?q={uuid}')
    except exceptions.Unauthorized:
        return RedirectResponse(request.url_for('unauthorized') + f'?q={uuid}')

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

    return dep.templates.TemplateResponse('delete_item.html', context)
