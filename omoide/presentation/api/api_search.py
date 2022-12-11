# -*- coding: utf-8 -*-
"""Search related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.infra.special_types import Success
from omoide.presentation import dependencies as dep
from omoide.presentation import utils
from omoide.presentation import web

router = APIRouter(prefix='/api/search')


@router.get('')
async def api_search(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.ApiSearchUseCase = Depends(
            dep.api_search_use_case),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
):
    """Return portion of random items."""
    result = await use_case.execute(user, aim_wrapper.aim)

    items = []
    if isinstance(result, Success):
        items = utils.to_simple_items(request, result.value)

    return items


@router.get('/suggest')
async def api_suggest_tag(
        user: domain.User = Depends(dep.get_current_user),
        text: str = '',
        use_case: use_cases.ApiSuggestTagUseCase = Depends(
            dep.api_suggest_tag_use_case),
):
    """Help user by suggesting possible tags."""
    variants: list[str] = []

    if len(text) > 1:
        result = await use_case.execute(user, domain.GuessTag(text=text))

        if isinstance(result, Success):
            variants = [x.tag for x in result.value]

    return {
        'variants': variants,
    }
