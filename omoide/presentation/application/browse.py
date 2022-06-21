# -*- coding: utf-8 -*-
"""Browse related routes.
"""
import fastapi
from fastapi import Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse

from omoide import domain
from omoide import use_cases
from omoide.domain import exceptions
from omoide.presentation import dependencies as dep
from omoide.presentation import infra, constants
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/browse/{uuid}')
async def browse(
        request: Request,
        uuid: str,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.AppBrowseUseCase = Depends(
            dep.app_browse_use_case),
        config: Config = Depends(dep.config),
        response_class=HTMLResponse,
):
    """Browse contents of a single item as collection."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
    )

    query = infra.query_maker.from_request(request.query_params)
    aim = domain.aim_from_params(dict(request.query_params))

    try:
        valid_uuid = infra.parse.cast_uuid(uuid)
        result = await use_case.execute(user, valid_uuid, aim, details)
    except exceptions.IncorrectUUID:
        return RedirectResponse(request.url_for('bad_request'))
    except exceptions.NotFound:
        return RedirectResponse(request.url_for('not_found') + f'?q={uuid}')
    except exceptions.Unauthorized:
        return RedirectResponse(request.url_for('unauthorized') + f'?q={uuid}')
    except exceptions.Forbidden:
        return RedirectResponse(request.url_for('forbidden') + f'?q={uuid}')

    context = {
        'request': request,
        'config': config,
        'user': user,
        'uuid': uuid,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
        'location': result.location,
        'api_url': request.url_for('api_browse', uuid=uuid),
        'result': result,
        'current_item': result.item,
    }

    if result.paginated:
        template = 'browse_paginated.html'
        paginator = infra.Paginator(
            page=details.page,
            items_per_page=details.items_per_page,
            total_items=result.total_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )
        context['paginator'] = paginator
    else:
        template = 'browse_dynamic.html'

    return dep.templates.TemplateResponse(template, context)
