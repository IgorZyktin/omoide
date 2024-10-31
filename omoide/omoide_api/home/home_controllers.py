"""API operations that return detailed info on specific item groups."""

import time
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from omoide import const
from omoide import dependencies as dep
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.home import home_use_cases

api_home_router = APIRouter(prefix='/home', tags=['Home'])


@api_home_router.get(
    '',
    response_model=common_api_models.ManyItemsOutput,
)
async def api_home(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    order: Annotated[const.ORDER_TYPE, Query()] = const.RANDOM,
    collections: Annotated[bool, Query()] = False,
    direct: Annotated[bool, Query()] = False,
    last_seen: Annotated[int, Query()] = common_api_models.LAST_SEEN_DEFAULT,
    limit: Annotated[
        int,
        Query(
            ge=common_api_models.MIN_LIMIT,
            lt=common_api_models.MAX_LIMIT,
        ),
    ] = common_api_models.DEFAULT_LIMIT,
):
    """Return items for user home page.

    Combined collections of all available users.
    """
    start = time.perf_counter()
    use_case = home_use_cases.ApiHomeUseCase(mediator)

    items = await use_case.execute(
        user=user,
        order=order,
        collections=collections,
        direct=direct,
        last_seen=last_seen,
        limit=limit,
    )

    response = common_api_models.ManyItemsOutput(
        duration=0.0,
        items=[common_api_models.ItemOutput(**item.model_dump()) for item in items],
    )
    response.duration = time.perf_counter() - start
    return response
