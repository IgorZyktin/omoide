"""API operations that return detailed info on specific item groups."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from omoide import const
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.home import home_use_cases
from omoide import dependencies as dep

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
    use_case = home_use_cases.ApiHomeUseCase(mediator)

    duration, items, extras = await use_case.execute(
        user=user,
        order=order,
        collections=collections,
        direct=direct,
        last_seen=last_seen,
        limit=limit,
    )

    return common_api_models.ManyItemsOutput(
        duration=duration,
        items=[
            common_api_models.ItemOutput(
                **utils.serialize(item.model_dump()),
                extras=utils.serialize(item_extras),
            )
            for item, item_extras in zip(items, extras, strict=False)
        ],
    )
