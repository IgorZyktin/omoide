# -*- coding: utf-8 -*-
"""Search related routes.
"""
from typing import Type

import fastapi
from fastapi import Depends
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response

from omoide import domain
from omoide import use_cases
from omoide.infra.special_types import Failure
from omoide.infra.special_types import Success
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import utils
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/search')
async def app_search(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.AppSearchUseCase = Depends(
            dep.get_search_use_case),
        config: Config = Depends(dep.config),
        response_class: Type[Response] = HTMLResponse,
):
    """Main page of the application."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
        items_per_page_async=constants.ITEMS_PER_UPLOAD,
    )

    query = infra.query_maker.from_request(request.query_params)
    aim = domain.aim_from_params(dict(request.query_params))

    _result = await use_case.execute(user, query, details)

    if isinstance(_result, Failure):
        return web.redirect_from_error(request, _result.error)

    result, is_random = _result.value

    if is_random:
        template = 'search_dynamic.html'
        paginator = None
    else:
        template = 'search.html'
        paginator = infra.Paginator(
            page=result.page,
            items_per_page=details.items_per_page,
            total_items=result.total_items,
            pages_in_block=constants.PAGES_IN_BLOCK,
        )

    context = {
        'request': request,
        'config': config,
        'user': user,
        'aim': aim,
        'query': infra.query_maker.QueryWrapper(query, details),
        'details': details,
        'paginator': paginator,
        'result': result,
    }

    return dep.templates.TemplateResponse(template, context)


@router.get('/api/random/{items_per_page}')
async def api_random(
        request: Request,
        items_per_page: int,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.AppSearchUseCase = Depends(
            dep.get_search_use_case),
):
    """Return portion of random items."""
    # TODO - random can return repeating items
    details = domain.Details(page=1, anchor=-1, items_per_page=items_per_page)
    query = domain.Query(raw_query='', tags_include=[], tags_exclude=[])
    _result = await use_case.execute(user, query, details)
    if isinstance(_result, Success):
        result, _ = _result.value
        return utils.to_simple_items(request, result.items)
    return []
