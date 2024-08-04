"""API operations that return detailed info on specific item groups."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from omoide import const
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api.browse import browse_api_models
from omoide.omoide_api.browse import browse_use_cases
from omoide.omoide_api.common import common_api_models
from omoide.presentation import dependencies as dep

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
    last_seen: Annotated[int, Query()] = browse_api_models.LAST_SEEN_DEFAULT,
    limit: Annotated[int, Query(
        ge=browse_api_models.BROWSE_MIN_LIMIT,
        lt=browse_api_models.BROWSE_MAX_LIMIT,
    )] = browse_api_models.BROWSE_DEFAULT_LIMIT,
):
    """Perform browse request.

    Returns all descendants of a specified item.
    """
    use_case = browse_use_cases.ApiBrowseUseCase(mediator)

    duration, items, extras = await use_case.execute(
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
        items=[
            common_api_models.ItemOutput(
                **utils.serialize(item.model_dump()),
                extras=utils.serialize(item_extras),
            )
            for item, item_extras in zip(items, extras)
        ]
    )
