"""User related API operations.
"""
from fastapi import APIRouter
from fastapi import Depends

from omoide import domain
from omoide.infra.mediator import Mediator
from omoide.omoide_api import use_cases
from omoide.omoide_api.controllers import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

users_router = APIRouter()


@users_router.get('/users')
async def api_get_users(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get list of users."""
    use_case = use_cases.GetUsersUseCase(mediator)

    try:
        users, extras = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)

    return [
        models.UserOutput(
            **web.serialize(user.model_dump()),
            extra=web.serialize(extra),
        )
        for user, extra in zip(users, extras)
    ]
