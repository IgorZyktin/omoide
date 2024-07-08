"""API operations that process commands from users."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.input import input_api_models
from omoide.omoide_api.input import input_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

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
        variants = await use_case.execute(user, tag)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return input_api_models.AutocompleteOutput(variants=variants)
