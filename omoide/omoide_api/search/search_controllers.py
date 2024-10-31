"""API operations that process textual requests from users."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from omoide import const
from omoide import custom_logging
from omoide import dependencies as dep
from omoide import limits
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.search import search_api_models
from omoide.omoide_api.search import search_use_cases

LOG = custom_logging.get_logger(__name__)

api_search_router = APIRouter(prefix='/search', tags=['Search'])


@api_search_router.get(
    '/autocomplete',
    status_code=status.HTTP_200_OK,
    response_model=search_api_models.AutocompleteOutput,
)
async def api_autocomplete(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    tag: Annotated[str, Query(max_length=limits.MAX_QUERY)] = limits.DEF_QUERY,
    limit: Annotated[
        int,
        Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT),
    ] = limits.AUTOCOMPLETE_LIMIT,
):
    """Return tags that match supplied string.

    You will get list of strings, ordered by their frequency.
    Most popular tags will be at the top.

    This endpoint can be used by anybody, but each user will get tailored
    output. String must be an exact match, no guessing is used.
    """
    use_case = search_use_cases.AutocompleteUseCase(mediator)

    # noinspection PyBroadException
    try:
        variants = await use_case.execute(
            user=user,
            tag=tag,
            minimal_length=limits.MIN_AUTOCOMPLETE,
            limit=limit,
        )
    except Exception:
        LOG.exception(
            'Failed to perform autocompletion for user {} and input {!r}',
            user,
            tag,
        )
        variants = []

    return search_api_models.AutocompleteOutput(variants=variants)


@api_search_router.get(
    '/recent_updates',
    status_code=status.HTTP_200_OK,
    response_model=search_api_models.RecentUpdatesOutput,
)
async def api_get_recent_updates(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    order: Annotated[const.ORDER_TYPE, Query()] = const.RANDOM,
    collections: Annotated[bool, Query()] = False,
    last_seen: Annotated[int, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
):
    """Return recently updated items.

    Request will find when newest item was updated.
    And then return all items uploaded at that day.

    This endpoint can be used by any registered user,
    but each will get tailored output.
    """
    use_case = search_use_cases.RecentUpdatesUseCase(mediator)

    items, users = await use_case.execute(
        user=user,
        order=order,
        collections=collections,
        last_seen=last_seen,
        limit=limit,
    )

    return search_api_models.RecentUpdatesOutput(
        items=common_api_models.convert_items(items, users)
    )


@api_search_router.get(
    '/total',
    response_model=search_api_models.SearchTotalOutput,
)
async def api_search_total(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    q: Annotated[str, Query(max_length=limits.MAX_QUERY)] = limits.DEF_QUERY,
    collections: Annotated[bool, Query()] = False,
):
    """Return total amount of items that correspond to search query."""
    use_case = search_use_cases.ApiSearchTotalUseCase(mediator)

    total, duration = await use_case.execute(
        user=user,
        query=q,
        minimal_length=limits.MIN_QUERY,
        collections=collections,
    )

    return search_api_models.SearchTotalOutput(total=total, duration=duration)


@api_search_router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_search(  # noqa: PLR0913
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    q: Annotated[str, Query(max_length=limits.MAX_QUERY)] = limits.DEF_QUERY,
    order: Annotated[const.ORDER_TYPE, Query()] = const.RANDOM,
    collections: Annotated[bool, Query()] = False,
    last_seen: Annotated[int, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
):
    """Perform search request.

    Given input will be split into tags.
    For example 'cats + dogs - frogs' will be treated as
    [must include 'cats', must include 'dogs', must not include 'frogs'].
    """
    use_case = search_use_cases.ApiSearchUseCase(mediator)

    duration, items, users = await use_case.execute(
        user=user,
        query=q,
        minimal_length=limits.MIN_QUERY,
        collections=collections,
        order=order,
        last_seen=last_seen,
        limit=limit,
    )

    return common_api_models.ManyItemsOutput(
        duration=duration,
        items=common_api_models.convert_items(items, users),
    )
