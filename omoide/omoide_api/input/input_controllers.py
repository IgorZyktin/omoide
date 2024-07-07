"""API operations that process commands from users."""
import http

from fastapi import APIRouter
from fastapi import Depends

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.input import input_api_models
from omoide.omoide_api.input import input_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

input_router = APIRouter(prefix='/input', tags=['input'])


@input_router.get(
    '/autocomplete',
    status_code=http.HTTPStatus.OK,
    response_model=input_api_models.AutocompleteOutput,
)
async def api_autocomplete(
    user: models.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
    tag: str = '',
):
    """Return tags that match supplied string."""
    try:
        use_case = input_use_cases.AutocompleteUseCase(mediator)
        variants = await use_case.execute(user, tag)
    except Exception as exc:
        web.raise_from_exc(exc)

    return input_api_models.AutocompleteOutput(variants=variants)
