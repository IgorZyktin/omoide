# -*- coding: utf-8 -*-
"""Profile related API operations.
"""
import fastapi
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/api/profile/new')
async def api_profile_new(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.APIProfileNewUseCase = Depends(
            dep.profile_new_use_case,
        ),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
        templates: web.TemplateEngine = Depends(dep.get_templates),
):
    """Return portion of recently loaded items."""
    result = await use_case.execute(user, aim_wrapper.aim)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    items, names = result.value
    return web.items_to_dict(
        request, templates, items, names, config.prefix_size)
