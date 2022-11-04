# -*- coding: utf-8 -*-
"""Home page related API operations.
"""
import fastapi

from omoide import domain
from omoide import use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import utils

router = fastapi.APIRouter()


@router.get('/api/home')
async def api_home(
        request: fastapi.Request,
        user: domain.User = fastapi.Depends(dep.get_current_user),
        use_case: use_cases.AppHomeUseCase = fastapi.Depends(
            dep.app_home_use_case),
):
    """Return portion of items for home directory."""
    aim = domain.aim_from_params(dict(request.query_params))
    result = await use_case.execute(user, aim)
    return utils.to_simple_items(request, result.value)
