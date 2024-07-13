"""Home page related operations."""
from typing import Annotated

import fastapi
from fastapi import Depends
from starlette.requests import Request

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_app.home import home_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web
from omoide.presentation.app_config import Config

home_router = fastapi.APIRouter()


@home_router.get('/api/home')
async def api_home(
    request: Request,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    config: Annotated[Config, Depends(dep.get_config)],
    aim_wrapper: Annotated[web.AimWrapper, Depends(dep.get_aim)],
):
    """Return portion of items for home directory."""
    use_case = home_use_cases.GetHomePageItemsUseCase(mediator)
    items, names = await use_case.execute(user, aim_wrapper.aim)
    return web.items_to_dict(request, items, names, config.prefix_size)
