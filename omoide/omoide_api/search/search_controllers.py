"""API operations that process textual requests from users."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from omoide import const
from omoide import custom_logging
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.search import search_api_models
from omoide.omoide_api.search import search_use_cases
from omoide.presentation import dependencies as dep

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
    tag: Annotated[str, Query(
        max_length=common_api_models.MAX_LENGTH_DEFAULT,
    )] = common_api_models.QUERY_DEFAULT,
    limit: Annotated[int, Query(
        ge=common_api_models.MIN_LIMIT,
        lt=common_api_models.MAX_LIMIT,
    )] = common_api_models.AUTOCOMPLETE_LIMIT,
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
            minimal_length=common_api_models.AUTOCOMPLETE_MIN_LENGTH,
            limit=limit,
        )
    except Exception:
        LOG.exception(
            'Failed to perform autocompletion for user {} and input {!r}',
            user,
            tag
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
    last_seen: Annotated[int, Query()] = common_api_models.LAST_SEEN_DEFAULT,
    limit: Annotated[int, Query(
        ge=common_api_models.MIN_LIMIT,
        lt=common_api_models.MAX_LIMIT,
    )] = common_api_models.DEFAULT_LIMIT,
):
    """Return recently updated items.

    Request will find when newest item was updated.
    And then return all items uploaded at that day.

    This endpoint can be used by any registered user,
    but each will get tailored output.
    """
    use_case = search_use_cases.RecentUpdatesUseCase(mediator)

    items, parent_names = await use_case.execute(
        user=user,
        order=order,
        collections=collections,
        last_seen=last_seen,
        limit=limit,
    )

    return search_api_models.RecentUpdatesOutput(
        items=[
            common_api_models.ItemOutput(
                **item.model_dump(),
                extras={'parent_name': parent_name}
            )
            for item, parent_name in zip(items, parent_names, strict=False)
        ],
    )


@api_search_router.get(
    '/total',
    response_model=search_api_models.SearchTotalOutput,
)
async def api_search_total(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    q: Annotated[str, Query(
        max_length=common_api_models.MAX_LENGTH_DEFAULT,
    )] = common_api_models.QUERY_DEFAULT,
    collections: Annotated[bool, Query()] = False,
):
    """Return total amount of items that correspond to search query."""
    use_case = search_use_cases.ApiSearchTotalUseCase(mediator)

    total, duration = await use_case.execute(
        user=user,
        query=q,
        minimal_length=common_api_models.MIN_LENGTH_DEFAULT,
        collections=collections,
    )

    return search_api_models.SearchTotalOutput(
        total=total,
        duration=duration,
    )


@api_search_router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_search(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    q: Annotated[str, Query(
        max_length=common_api_models.MAX_LENGTH_DEFAULT,
    )] = common_api_models.QUERY_DEFAULT,
    order: Annotated[const.ORDER_TYPE, Query()] = const.RANDOM,
    collections: Annotated[bool, Query()] = False,
    last_seen: Annotated[int, Query()] = common_api_models.LAST_SEEN_DEFAULT,
    limit: Annotated[int, Query(
        ge=common_api_models.MIN_LIMIT,
        lt=common_api_models.MAX_LIMIT,
    )] = common_api_models.DEFAULT_LIMIT,
):
    """Perform search request.

    Given input will be split into tags.
    For example 'cats + dogs - frogs' will be treated as
    [must include 'cats', must include 'dogs', must not include 'frogs'].
    """
    use_case = search_use_cases.ApiSearchUseCase(mediator)

    duration, items, extras = await use_case.execute(
        user=user,
        query=q,
        minimal_length=common_api_models.MIN_LENGTH_DEFAULT,
        collections=collections,
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
            for item, item_extras in zip(items, extras, strict=False)
        ]
    )
