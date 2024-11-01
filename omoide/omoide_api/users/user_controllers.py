"""User related API operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status

from omoide import dependencies as dep
from omoide import models
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api.users import user_api_models
from omoide.omoide_api.users import user_use_cases
from omoide.presentation import web

api_users_router = APIRouter(prefix='/users', tags=['Users'])


@api_users_router.post(
    '',
    status_code=status.HTTP_201_CREATED,
    response_model=user_api_models.UserOutput,
)
async def api_create_user(
    request: Request,
    response: Response,
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    user_in: user_api_models.UserInput,
):
    """Create new user.

    Only admins can do this.
    """
    use_case = user_use_cases.CreateUserUseCase(mediator)

    try:
        user_out = await use_case.execute(
            admin=admin,
            name=user_in.name,
            login=user_in.login,
            password=user_in.password,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    response.headers['Location'] = str(
        request.url_for('api_get_user_by_uuid', user_uuid=user_out.uuid)
    )

    return user_api_models.UserOutput(**utils.serialize(user_out.model_dump()))


@api_users_router.get(
    '',
    status_code=status.HTTP_200_OK,
    response_model=user_api_models.UserCollectionOutput,
)
async def api_get_all_users(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get list of users.

    Admins can get all users, registered users will get only themselves.
    """
    use_case = user_use_cases.GetAllUsersUseCase(mediator)

    try:
        users = await use_case.execute(user)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'users': [
            user_api_models.UserOutput(**utils.serialize(user.model_dump())) for user in users
        ]
    }


@api_users_router.get(
    '/{uuid}/resource_usage',
    status_code=status.HTTP_200_OK,
    response_model=user_api_models.UserResourceUsageOutput,
)
async def api_get_user_resource_usage(
    user_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get resource usage info for specific user."""
    use_case = user_use_cases.GetUserResourceUsageUseCase(mediator)

    try:
        output = await use_case.execute(user, user_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return user_api_models.UserResourceUsageOutput(
        user_uuid=str(output.user_uuid),
        total_items=output.total_items,
        total_collections=output.total_collections,
        content_bytes=output.disk_usage.content_bytes,
        content_hr=output.disk_usage.content_hr,
        preview_bytes=output.disk_usage.preview_bytes,
        preview_hr=output.disk_usage.preview_hr,
        thumbnail_bytes=output.disk_usage.thumbnail_bytes,
        thumbnail_hr=output.disk_usage.thumbnail_hr,
    )


@api_users_router.get(
    '/anon/known_tags',
    status_code=status.HTTP_200_OK,
    response_model=dict[str, int],
)
async def api_get_anon_tags(mediator: Annotated[Mediator, Depends(dep.get_mediator)]):
    """Get all known tags for anon user."""
    use_case = user_use_cases.GetAnonUserTagsUseCase(mediator)

    try:
        tags = await use_case.execute()
    except Exception as exc:
        return web.raise_from_exc(exc)

    return tags


@api_users_router.get(
    '/{uuid}/known_tags',
    status_code=status.HTTP_200_OK,
    response_model=dict[str, int],
)
async def api_get_user_tags(
    user_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get all known tags for specific user."""
    use_case = user_use_cases.GetKnownUserTagsUseCase(mediator)

    try:
        tags = await use_case.execute(user, user_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return tags


@api_users_router.get(
    '/{uuid}',
    status_code=status.HTTP_200_OK,
    response_model=user_api_models.UserOutput,
)
async def api_get_user_by_uuid(
    user_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Get user by UUID."""
    use_case = user_use_cases.GetUserByUUIDUseCase(mediator)

    try:
        user = await use_case.execute(user, user_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))


@api_users_router.put(
    '/{uuid}/name',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=user_api_models.UserOutput,
)
async def api_change_user_name(
    user_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    payload: user_api_models.UserValueInput,
):
    """Update name of existing user."""
    use_case = user_use_cases.ChangeUserNameUseCase(mediator)

    try:
        user = await use_case.execute(user, user_uuid, payload.value)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))


@api_users_router.put(
    '/{uuid}/login',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=user_api_models.UserOutput,
)
async def api_change_user_login(
    user_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    payload: user_api_models.UserValueInput,
):
    """Update login of existing user."""
    use_case = user_use_cases.ChangeUserLoginUseCase(mediator)

    try:
        user = await use_case.execute(user, user_uuid, payload.value)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))


@api_users_router.put(
    '/{uuid}/password',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=user_api_models.UserOutput,
)
async def api_change_user_password(
    user_uuid: UUID,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    payload: user_api_models.UserValueInput,
):
    """Update password of existing user."""
    use_case = user_use_cases.ChangeUserPasswordUseCase(mediator)

    try:
        user = await use_case.execute(user, user_uuid, payload.value)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))
