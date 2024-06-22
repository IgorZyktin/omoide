"""User related API operations.
"""
import http

from fastapi import APIRouter
from fastapi import Depends

from omoide import domain
from omoide.infra.mediator import Mediator
from omoide.omoide_api import use_cases
from omoide.omoide_api.controllers import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

users_router = APIRouter(tags=['users'])


@users_router.get(
    '/users',
    status_code=http.HTTPStatus.OK,
    response_model=list[models.UserOutput],
)
async def api_get_users(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get list of users.

    If you're anon, you will always get an empty list.
    If you're registered, you will get a list with only yourself.
    """
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
