# -*- coding: utf-8 -*-
"""Profile related API operations.
"""
import fastapi
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import utils
from omoide.presentation import web

router = fastapi.APIRouter()


@router.get('/api/profile/new')
async def api_profile_new(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.APIProfileNewUseCase = Depends(
            dep.profile_new_use_case,
        ),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
):
    """Return portion of recently loaded items."""
    result = await use_case.execute(user, aim_wrapper.aim)
    return utils.to_simple_items(request, result.value)
