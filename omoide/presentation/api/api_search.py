# -*- coding: utf-8 -*-
"""Search related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.infra.special_types import Success
from omoide.presentation import constants
from omoide.presentation import dependencies as dep
from omoide.presentation import infra
from omoide.presentation import utils

router = APIRouter(prefix='/api/search')


@router.get('')
async def api_search(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ApiSearchUseCase = Depends(
            dep.api_search_use_case),
):
    """Return portion of random items."""
    details = infra.parse.details_from_params(
        params=request.query_params,
        items_per_page=constants.ITEMS_PER_PAGE,
        items_per_page_async=constants.ITEMS_PER_UPLOAD,
    )

    aim = domain.aim_from_params(dict(request.query_params))
    query = infra.query_maker.from_request(request.query_params)

    result = await use_case.execute(user, query, details, aim)

    if isinstance(result, Success):
        return utils.to_simple_items(request, result.value)

    return []
