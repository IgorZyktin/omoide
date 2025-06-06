"""API operations that return detailed info on specific item groups."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from omoide import const
from omoide import dependencies as dep
from omoide import limits
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.home import home_use_cases
from omoide.presentation import web

api_home_router = APIRouter(prefix='/home', tags=['Home'])


@api_home_router.get(
    '',
    response_model=common_api_models.ManyItemsOutput,
)
async def api_home(  # noqa: PLR0913
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    order: Annotated[const.ORDER_TYPE, Query()] = const.DEF_ORDER,
    collections: Annotated[bool, Query()] = const.DEF_COLLECTIONS,
    direct: Annotated[bool, Query()] = const.DEF_DIRECT,
    last_seen: Annotated[int | None, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
):
    """Return items for user home page.

    Combined collections of all available users.
    """
    use_case = home_use_cases.ApiHomeUseCase(mediator)

    plan = models.Plan(
        query='',
        tags_include=set(),
        tags_exclude=set(),
        order=order,
        collections=collections,
        direct=direct,
        last_seen=last_seen,
        limit=limit,
    )

    try:
        items, users = await use_case.execute(user, plan)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return common_api_models.ManyItemsOutput(items=common_api_models.convert_items(items, users))
