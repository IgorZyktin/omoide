"""User related API operations."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import status

from omoide import dependencies as dep
from omoide import models
from omoide import utils
from omoide.database import interfaces as db_interfaces
from omoide.database.interfaces.abs_database import AbsDatabase
from omoide.infra import interfaces as infra_interfaces
from omoide.omoide_api.users import user_api_models
from omoide.omoide_api.users import user_use_cases

api_users_router = APIRouter(prefix='/users', tags=['Users'])


@api_users_router.post(
    '',
    summary='Create new user',
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {'description': 'Created'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
    },
    response_model=user_api_models.UserOutput,
)
async def api_create_user(  # noqa: PLR0913
    request: Request,
    response: Response,
    user_in: user_api_models.UserInput,
    admin: models.User = Depends(dep.get_admin_user),
    authenticator: infra_interfaces.AbsAuthenticator = Depends(dep.get_authenticator),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    items_repo: db_interfaces.AbsItemsRepo = Depends(dep.get_items_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
) -> user_api_models.UserOutput:
    """Create new user.

    Only admins can do this.
    """
    use_case = user_use_cases.CreateUserUseCase(
        authenticator, database, users_repo, items_repo, meta_repo, tags_repo
    )

    user_out = await use_case.execute(
        admin=admin,
        name=user_in.name,
        login=user_in.login,
        password=user_in.password,
    )

    response.headers['Location'] = str(
        request.url_for('api_get_user_by_uuid', user_uuid=user_out.uuid)
    )

    return user_api_models.UserOutput(**utils.serialize(user_out.model_dump()))


@api_users_router.get(
    '',
    summary='Get list of users',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {'description': 'Ok'},
    },
    response_model=user_api_models.UserCollectionOutput,
)
async def api_get_all_users(
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
) -> dict[str, Any]:
    """Get list of users.

    Admins can get all users, registered users will get only themselves.
    """
    use_case = user_use_cases.GetAllUsersUseCase(database, users_repo)

    users = await use_case.execute(user)

    return {
        'users': [
            user_api_models.UserOutput(**utils.serialize(user.model_dump())) for user in users
        ]
    }


@api_users_router.get(
    '/{user_uuid}/resource_usage',
    summary='Get resource usage info for specific user',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {'description': 'Ok'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=user_api_models.UserResourceUsageOutput,
)
async def api_get_user_resource_usage(
    user_uuid: UUID,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    meta_repo: db_interfaces.AbsMetaRepo = Depends(dep.get_meta_repo),
) -> user_api_models.UserResourceUsageOutput:
    """Get resource usage info for specific user."""
    use_case = user_use_cases.GetUserResourceUsageUseCase(database, users_repo, meta_repo)

    output = await use_case.execute(user, user_uuid)

    return user_api_models.UserResourceUsageOutput(
        user_uuid=str(output.user.uuid),
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
    summary='Get all known tags for anon user',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {'description': 'Ok'},
    },
    response_model=dict[str, int],
)
async def api_get_anon_tags(
    database: AbsDatabase = Depends(dep.get_database),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
) -> dict[str, int]:
    """Get all known tags for anon user."""
    use_case = user_use_cases.GetAnonUserTagsUseCase(database, tags_repo)

    return await use_case.execute()


@api_users_router.get(
    '/{user_uuid}/known_tags',
    summary='Get all known tags for specific user',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {'description': 'Ok'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=dict[str, int],
)
async def api_get_user_tags(
    user_uuid: UUID,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    tags_repo: db_interfaces.AbsTagsRepo = Depends(dep.get_tags_repo),
) -> dict[str, int]:
    """Get all known tags for specific user."""
    use_case = user_use_cases.GetKnownUserTagsUseCase(database, users_repo, tags_repo)

    return await use_case.execute(user, user_uuid)


@api_users_router.get(
    '/{user_uuid}',
    summary='Get user by UUID',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {'description': 'Ok'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=user_api_models.UserOutput,
)
async def api_get_user_by_uuid(
    user_uuid: UUID,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
) -> user_api_models.UserOutput:
    """Get user by UUID."""
    use_case = user_use_cases.GetUserByUUIDUseCase(database, users_repo)

    user = await use_case.execute(user, user_uuid)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))


@api_users_router.put(
    '/{user_uuid}/name',
    summary='Update name of existing user',
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Accepted'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=user_api_models.UserOutput,
)
async def api_change_user_name(
    user_uuid: UUID,
    payload: user_api_models.UserValueInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
    misc_repo: db_interfaces.AbsMiscRepo = Depends(dep.get_misc_repo),
) -> user_api_models.UserOutput:
    """Update name of existing user."""
    use_case = user_use_cases.ChangeUserNameUseCase(database, users_repo, misc_repo)

    user = await use_case.execute(user, user_uuid, payload.value)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))


@api_users_router.put(
    '/{user_uuid}/login',
    summary='Update login of existing user',
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Accepted'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=user_api_models.UserOutput,
)
async def api_change_user_login(
    user_uuid: UUID,
    payload: user_api_models.UserValueInput,
    user: models.User = Depends(dep.get_known_user),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
) -> user_api_models.UserOutput:
    """Update login of existing user."""
    use_case = user_use_cases.ChangeUserLoginUseCase(database, users_repo)

    user = await use_case.execute(user, user_uuid, payload.value)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))


@api_users_router.put(
    '/{user_uuid}/password',
    summary='Update password of existing user',
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {'description': 'Accepted'},
        status.HTTP_403_FORBIDDEN: {'description': 'Permission denied'},
        status.HTTP_404_NOT_FOUND: {'description': 'Object does not exist'},
    },
    response_model=user_api_models.UserOutput,
)
async def api_change_user_password(
    user_uuid: UUID,
    payload: user_api_models.UserValueInput,
    user: models.User = Depends(dep.get_known_user),
    authenticator: infra_interfaces.AbsAuthenticator = Depends(dep.get_authenticator),
    database: AbsDatabase = Depends(dep.get_database),
    users_repo: db_interfaces.AbsUsersRepo = Depends(dep.get_users_repo),
) -> user_api_models.UserOutput:
    """Update password of existing user."""
    use_case = user_use_cases.ChangeUserPasswordUseCase(authenticator, database, users_repo)

    user = await use_case.execute(user, user_uuid, payload.value)

    return user_api_models.UserOutput(**utils.serialize(user.model_dump()))
