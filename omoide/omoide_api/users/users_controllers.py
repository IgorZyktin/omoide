"""User related API operations."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api.users import users_api_models
from omoide.omoide_api.users import users_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

users_router = APIRouter(prefix='/users', tags=['users'])


@users_router.get(
    '/{uuid}/stats',
    status_code=status.HTTP_200_OK,
    response_model=users_api_models.UserStatsOutput,
)
async def api_get_user_stats(
    uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get statistics for specific user."""
    use_case = users_use_cases.GetUserStatsUseCase(mediator)

    try:
        output = await use_case.execute(user, uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return users_api_models.UserStatsOutput(
        total_items=output['total_items'],
        total_collections=output['total_collections'],
        content_bytes=output['content_bytes'],
        content_hr=utils.byte_count_to_text(output['content_bytes']),
        preview_bytes=output['preview_bytes'],
        preview_hr=utils.byte_count_to_text(output['preview_bytes']),
        thumbnail_bytes=output['thumbnail_bytes'],
        thumbnail_hr=utils.byte_count_to_text(output['thumbnail_bytes']),
    )


@users_router.get(
    '/{uuid}/tags',
    status_code=status.HTTP_200_OK,
    response_model=dict[str, int],
)
async def api_get_user_tags(
    uuid: str,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get all known tags for specific user.

    You can also pass 'anon' as UUID to get tags for anonymous user.
    """
    use_case = users_use_cases.GetUserTagsUseCase(mediator)

    try:
        tags = await use_case.execute(user, uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return tags


@users_router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=users_api_models.UserCollectionOutput,
)
async def api_get_all_users(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    login: str | None = None,
):
    """Get list of users."""
    use_case = users_use_cases.GetAllUsersUseCase(mediator)

    try:
        users, extras = await use_case.execute(user, login)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'users': [
            users_api_models.UserOutput(
                **web.serialize(user.model_dump()),
                extra={
                    'root_item': web.to_simple_type(extras.get(user.uuid))
                },
            )
            for user in users
        ]
    }


@users_router.get(
    '/{uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=users_api_models.UserOutput,
)
async def api_get_user_by_uuid(
    uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_current_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get user by UUID."""
    use_case = users_use_cases.GetUserByUUIDUseCase(mediator)

    try:
        user, extra = await use_case.execute(user, uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return users_api_models.UserOutput(
        **web.serialize(user.model_dump()),
        extra=web.serialize(extra),
    )
