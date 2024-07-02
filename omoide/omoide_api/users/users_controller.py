"""User related API operations."""
import http
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from omoide import domain
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api.users import models
from omoide.omoide_api.users import users_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

user_router = APIRouter(prefix='/user', tags=['user'])
users_router = APIRouter(prefix='/users', tags=['users'])


@user_router.get(
    '/stats',
    status_code=http.HTTPStatus.OK,
    response_model=models.UserStatsOutput,
)
async def api_get_current_user_stats(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get statistics for current user."""
    use_case = users_use_cases.GetCurrentUserStatsUseCase(mediator)

    try:
        output = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return models.UserStatsOutput(
        total_items=output['total_items'],
        total_collections=output['total_collections'],
        content_bytes=output['content_bytes'],
        content_hr=utils.byte_count_to_text(output['content_bytes']),
        preview_bytes=output['preview_bytes'],
        preview_hr=utils.byte_count_to_text(output['preview_bytes']),
        thumbnail_bytes=output['thumbnail_bytes'],
        thumbnail_hr=utils.byte_count_to_text(output['thumbnail_bytes']),
    )


@user_router.get(
    '/tags',
    status_code=http.HTTPStatus.OK,
    response_model=dict[str, int],
)
async def api_get_current_user_tags(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get all known tags for current user."""
    use_case = users_use_cases.GetCurrentUserTagsUseCase(mediator)

    try:
        tags = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return tags


@users_router.get(
    '',
    status_code=http.HTTPStatus.OK,
    response_model=list[models.UserOutput],
)
async def api_get_all_users(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get list of users.

    If you're anon, you will always get an empty list.
    If you're registered, you will get a list with only yourself.
    """
    use_case = users_use_cases.GetAllUsersUseCase(mediator)

    try:
        users, extras = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return [
        models.UserOutput(
            **web.serialize(user.model_dump()),
            extra=web.serialize(extra),
        )
        for user, extra in zip(users, extras)
    ]


@users_router.get(
    '/{uuid}',
    status_code=http.HTTPStatus.OK,
    response_model=models.UserOutput,
)
async def api_get_user_by_uuid(
    uuid: UUID,
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get user by UUID."""
    use_case = users_use_cases.GetUserByUUIDUseCase(mediator)

    try:
        user, extra = await use_case.execute(user, uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return models.UserOutput(
        **web.serialize(user.model_dump()),
        extra=web.serialize(extra),
    )
