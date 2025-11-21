"""API operations that return detailed info on specific item groups."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from omoide import const
from omoide import dependencies as dep
from omoide import limits
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.browse import browse_use_cases
from omoide.omoide_api.common import common_api_models
from omoide.presentation import web

api_browse_router = APIRouter(prefix='/browse', tags=['Browse'])


@api_browse_router.get(
    '/{item_uuid}',
    summary='Perform browse request',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_browse(  # noqa: PLR0913
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_uuid: UUID,
    direct: Annotated[bool, Query()] = False,
    order: Annotated[const.ORDER_TYPE, Query()] = const.DEF_ORDER,
    collections: Annotated[bool, Query()] = const.DEF_COLLECTIONS,
    last_seen: Annotated[int | None, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_BROWSE, lt=limits.MAX_BROWSE)] = limits.DEF_BROWSE,
):
    """Perform browse request.

    Returns all descendants of a specified item.
    """
    use_case = browse_use_cases.ApiBrowseUseCase(mediator)

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
        duration, items, users = await use_case.execute(user, item_uuid, plan)
    except Exception as exc:
        return web.response_from_exc(exc)

    return common_api_models.ManyItemsOutput(
        duration=duration,
        items=common_api_models.convert_items(items, users),
    )
