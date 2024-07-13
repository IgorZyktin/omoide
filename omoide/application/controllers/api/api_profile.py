"""Profile related API operations."""
from typing import Annotated

import fastapi
from fastapi import Depends
from fastapi import Request

from omoide import models
from omoide import use_cases
from omoide.infra.special_types import Failure
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = fastapi.APIRouter(prefix='/api/profile')


@router.get('/new')
async def api_profile_new(
        request: Request,
        user: Annotated[models.User, Depends(dep.get_known_user)],
        use_case: Annotated[use_cases.APIProfileNewUseCase,
                            Depends(dep.profile_new_use_case)],
        aim_wrapper: web.AimWrapper = Depends(dep.get_aim),
):
    """Return portion of recently loaded items."""
    result = await use_case.execute(user, aim_wrapper.aim)

    if isinstance(result, Failure):
        web.raise_from_error(result.error)

    items, names = result.value
    return web.items_to_dict(request, items, names)
