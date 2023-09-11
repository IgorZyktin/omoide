"""Home page related API operations.
"""
import fastapi
from fastapi import Depends
from starlette.requests import Request

from omoide import domain
from omoide import use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

router = fastapi.APIRouter()


@router.get('/api/home')
async def api_home(
        request: Request,
        user: domain.User = Depends(dep.get_current_user),
        use_case: use_cases.AppHomeUseCase = Depends(dep.app_home_use_case),
        config: Config = Depends(dep.get_config),
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
):
    """Return portion of items for home directory."""
    result = await use_case.execute(user, aim_wrapper.aim)
    items, names = result.value
    return web.items_to_dict(request, items, names, config.prefix_size)
