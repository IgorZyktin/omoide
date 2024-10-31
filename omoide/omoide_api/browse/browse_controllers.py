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

api_browse_router = APIRouter(prefix='/browse', tags=['Browse'])


@api_browse_router.get(
    '/{item_uuid}',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_browse(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_uuid: UUID,
    direct: Annotated[bool, Query()] = False,
    order: Annotated[const.ORDER_TYPE, Query()] = const.RANDOM,
    collections: Annotated[bool, Query()] = False,
    last_seen: Annotated[int, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_BROWSE, lt=limits.MAX_BROWSE)] = limits.DEF_BROWSE,
):
    """Perform browse request.

    Returns all descendants of a specified item.
    """
    use_case = browse_use_cases.ApiBrowseUseCase(mediator)

    duration, items, users = await use_case.execute(
        user=user,
        item_uuid=item_uuid,
        collections=collections,
        direct=direct,
        order=order,
        last_seen=last_seen,
        limit=limit,
    )

    return common_api_models.ManyItemsOutput(
        duration=duration,
        items=common_api_models.convert_items(items, users),
    )
