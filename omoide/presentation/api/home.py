# -*- coding: utf-8 -*-
"""Home page related API operations.
"""
import fastapi

from omoide import domain, use_cases
from omoide.presentation import dependencies as dep, utils

router = fastapi.APIRouter()


@router.get('/api/home')
async def api_home(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.HomeUseCase = fastapi.Depends(
            dep.app_home_use_case),
):
    """Return portion of items for home directory."""
    aim = domain.aim_from_params(dict(request.query_params))
    items = await use_case.execute(user, aim)
    return utils.to_simple_items(request, items)
