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
from omoide import utils
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.omoide_api.common import common_api_models
from omoide.omoide_api.search import search_api_models
from omoide.omoide_api.search import search_use_cases

LOG = custom_logging.get_logger(__name__)

api_search_router = APIRouter(prefix='/search', tags=['Search'])


@api_search_router.get(
    '/autocomplete',
    summary='Return tags that match supplied string',
    status_code=status.HTTP_200_OK,
    response_model=search_api_models.AutocompleteOutput,
)
async def api_autocomplete(
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
    tag: Annotated[str, Query(max_length=limits.MAX_QUERY)] = limits.DEF_QUERY,
    limit: Annotated[
        int,
        Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT),
    ] = limits.AUTOCOMPLETE_LIMIT,
) -> search_api_models.AutocompleteOutput:
    """Return tags that match supplied string.

    You will get list of strings, ordered by their frequency.
    Most popular tags will be at the top.

    This endpoint can be used by anybody, but each user will get tailored
    output. String must be an exact match, no guessing is used.
    """
    use_case = search_use_cases.AutocompleteUseCase(database, tags_repo)

    # noinspection PyBroadException
    try:
        # Autocomplete swallows errors on purpose: the dropdown should
        # quietly degrade to "no suggestions" rather than show a stack
        # trace, so this endpoint stays out of the global error handler.
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
    summary='Return recently updated items',
    status_code=status.HTTP_200_OK,
    response_model=search_api_models.RecentUpdatesOutput,
)
async def api_get_recent_updates(  # noqa: PLR0913
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    browse_repo: db_interfaces.AbsBrowseRepo = Depends(dep.get_browse_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    order: Annotated[const.ORDER_TYPE, Query()] = const.DEF_ORDER,
    collections: Annotated[bool, Query()] = const.DEF_COLLECTIONS,
    last_seen: Annotated[int | None, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
) -> search_api_models.RecentUpdatesOutput:
    """Return recently updated items.

    This endpoint can be used by any user, but each will get tailored output.
    """
    use_case = search_use_cases.RecentUpdatesUseCase(database, browse_repo, users_repo)

    plan = models.Plan(
        query='',
        tags_include=set(),
        tags_exclude=set(),
        order=order,
        collections=collections,
        direct=False,
        last_seen=last_seen,
        limit=limit,
    )

    result = await use_case.execute(user, plan)

    return search_api_models.RecentUpdatesOutput(
        items=common_api_models.convert_items(result.items, result.users_map)
    )


@api_search_router.get(
    '/total',
    summary='Return total amount of items that correspond to search query',
    response_model=search_api_models.SearchTotalOutput,
)
async def api_search_total(
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    search_repo: db_interfaces.AbsSearchRepo = Depends(dep.get_search_repo),
    q: Annotated[str, Query(max_length=limits.MAX_QUERY)] = limits.DEF_QUERY,
    collections: Annotated[bool, Query()] = False,
) -> search_api_models.SearchTotalOutput:
    """Return total amount of items that correspond to search query."""
    if len(q) < limits.MIN_QUERY:
        return search_api_models.SearchTotalOutput(total=0, duration=0.0)

    use_case = search_use_cases.ApiSearchTotalUseCase(database, search_repo)
    tags_include, tags_exclude = utils.parse_tags(q)

    plan = models.Plan(
        query=q,
        tags_include=tags_include,
        tags_exclude=tags_exclude,
        order=const.ASC,
        collections=collections,
        direct=False,
        last_seen=None,
        limit=-1,
    )

    result = await use_case.execute(user, plan)

    return search_api_models.SearchTotalOutput(total=result.total, duration=result.duration)


@api_search_router.get(
    '',
    summary='Perform search request',
    status_code=status.HTTP_200_OK,
    response_model=common_api_models.ManyItemsOutput,
)
async def api_search(  # noqa: PLR0913
    user: models.User = Depends(dep.get_current_user),
    database: AbsDatabase = Depends(dep.get_database),
    search_repo: db_interfaces.AbsSearchRepo = Depends(dep.get_search_repo),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    q: Annotated[str, Query(max_length=limits.MAX_QUERY)] = limits.DEF_QUERY,
    order: Annotated[const.ORDER_TYPE, Query()] = const.DEF_ORDER,
    collections: Annotated[bool, Query()] = const.DEF_COLLECTIONS,
    last_seen: Annotated[int | None, Query()] = limits.DEF_LAST_SEEN,
    limit: Annotated[int, Query(ge=limits.MIN_LIMIT, lt=limits.MAX_LIMIT)] = limits.DEF_LIMIT,
) -> common_api_models.ManyItemsOutput:
    """Perform search request.

    Given input will be split into tags.
    For example 'cats + dogs - frogs' will be treated as
    [must include 'cats', must include 'dogs', must not include 'frogs'].
    """
    if len(q) < limits.MIN_QUERY:
        return common_api_models.ManyItemsOutput(duration=0.0, items=[])

    use_case = search_use_cases.ApiSearchUseCase(database, search_repo, users_repo)
    tags_include, tags_exclude = utils.parse_tags(q)

    plan = models.Plan(
        query=q,
        tags_include=tags_include,
        tags_exclude=tags_exclude,
        order=order,
        collections=collections,
        direct=False,
        last_seen=last_seen,
        limit=limit,
    )

    result = await use_case.execute(user, plan)

    return common_api_models.ManyItemsOutput(
        duration=result.duration,
        items=common_api_models.convert_items(result.items, result.users_map),
    )
