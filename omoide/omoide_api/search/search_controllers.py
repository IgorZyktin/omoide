"""API operations that process textual requests from users."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra import custom_logging
from omoide.infra.mediator import Mediator
from omoide.omoide_api.search import search_api_models
from omoide.omoide_api.search import search_use_cases
from omoide.presentation import dependencies as dep

LOG = custom_logging.get_logger(__name__)

search_router = APIRouter(prefix='/search', tags=['Search'])


@search_router.get(
    '/autocomplete',
    status_code=status.HTTP_200_OK,
    response_model=search_api_models.AutocompleteOutput,
)
async def api_autocomplete(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    tag: str = '',
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
        shortened_tag = tag[:search_api_models.MAXIMUM_AUTOCOMPLETE_SIZE]
        variants = await use_case.execute(
            user=user,
            tag=shortened_tag,
            minimal_length=search_api_models.MINIMAL_AUTOCOMPLETE_SIZE,
            limit=search_api_models.AUTOCOMPLETE_VARIANTS,
        )
    except Exception:
        LOG.exception(
            'Failed to perform autocompletion for user {} and input {!r}',
            user,
            tag
        )
        variants = []

    return search_api_models.AutocompleteOutput(variants=variants)
