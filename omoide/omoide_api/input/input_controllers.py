"""API operations that process textual requests from users."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra import custom_logging
from omoide.infra.mediator import Mediator
from omoide.omoide_api.input import input_api_models
from omoide.omoide_api.input import input_use_cases
from omoide.presentation import dependencies as dep

LOG = custom_logging.get_logger(__name__)

input_router = APIRouter(prefix='/input', tags=['Input'])


@input_router.get(
    '/autocomplete',
    status_code=status.HTTP_200_OK,
    response_model=input_api_models.AutocompleteOutput,
)
async def api_autocomplete(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    tag: str = '',
):
    """Return tags that match supplied string."""
    use_case = input_use_cases.AutocompleteUseCase(mediator)

    try:
        variants = await use_case.execute(
            user=user,
            tag=tag[:input_api_models.MAXIMUM_AUTOCOMPLETE_SIZE],
            minimal_length=input_api_models.MINIMAL_AUTOCOMPLETE_SIZE,
            limit=input_api_models.AUTOCOMPLETE_VARIANTS,
        )
    except Exception:
        LOG.exception(
            'Failed to perform autocompletion for user {} and input {!r}',
            user,
            tag
        )
        variants = []

    return input_api_models.AutocompleteOutput(variants=variants)
