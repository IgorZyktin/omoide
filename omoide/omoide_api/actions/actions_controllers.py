"""Computationally heavy operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import dependencies as dep
from omoide import models
from omoide.database import interfaces as db_interfaces
from omoide.object_storage import interfaces as os_interfaces
from omoide.omoide_api.actions import actions_use_cases
from omoide.presentation import web

api_actions_router = APIRouter(prefix='/actions', tags=['Actions'])


@api_actions_router.post(
    '/rebuild_known_tags_for_anon',
    summary='Recalculate all known tags for anon user',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_known_tags_for_anon(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    database: Annotated[db_interfaces.AbsDatabase, Depends(dep.get_database)],
    misc_repo: Annotated[db_interfaces.AbsMiscRepo, Depends(dep.get_misc_repo)],
):
    """Recalculate all known tags for anon user."""
    use_case = actions_use_cases.RebuildKnownTagsForAnonUseCase(database, misc_repo)

    try:
        operation_id = await use_case.execute(user)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {
        'result': 'rebuilding known tags for anon',
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/rebuild_known_tags_for_user/{user_uuid}',
    summary='Recalculate all known tags for registered user',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_known_tags_for_user(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    database: Annotated[db_interfaces.AbsDatabase, Depends(dep.get_database)],
    misc_repo: Annotated[db_interfaces.AbsMiscRepo, Depends(dep.get_misc_repo)],
    users_repo: Annotated[db_interfaces.AbsUsersRepo, Depends(dep.get_users_repo)],
    user_uuid: UUID,
):
    """Recalculate all known tags for registered user."""
    use_case = actions_use_cases.RebuildKnownTagsForUserUseCase(database, misc_repo, users_repo)

    try:
        operation_id = await use_case.execute(user, user_uuid)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {
        'result': 'rebuilding known tags for user',
        'user_uuid': str(user_uuid),
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/rebuild_known_tags_for_all',
    summary='Recalculate all known tags for all users',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_known_tags_for_all(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    database: Annotated[db_interfaces.AbsDatabase, Depends(dep.get_database)],
    misc_repo: Annotated[db_interfaces.AbsMiscRepo, Depends(dep.get_misc_repo)],
):
    """Recalculate all known tags for all users."""
    use_case = actions_use_cases.RebuildKnownTagsForAllUseCase(database, misc_repo)

    try:
        operation_id = await use_case.execute(user)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {
        'result': 'rebuilding known tags for all users',
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/rebuild_computed_tags/{item_uuid}',
    summary='Recalculate all computed tags for specific user',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str | None],
)
async def api_action_rebuild_computed_tags(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    database: Annotated[db_interfaces.AbsDatabase, Depends(dep.get_database)],
    misc_repo: Annotated[db_interfaces.AbsMiscRepo, Depends(dep.get_misc_repo)],
    users_repo: Annotated[db_interfaces.AbsUsersRepo, Depends(dep.get_users_repo)],
    items_repo: Annotated[db_interfaces.AbsItemsRepo, Depends(dep.get_items_repo)],
    item_uuid: UUID,
):
    """Recalculate all computed tags for specific user.

    If `including_children` is set to True, this will also affect all
    descendants of the item. This operation potentially can take a lot of time.
    """
    use_case = actions_use_cases.RebuildComputedTagsForItemUseCase(
        database, misc_repo, users_repo, items_repo
    )

    try:
        owner, item, job_id = await use_case.execute(user, item_uuid)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {
        'result': 'Rebuilding computed tags',
        'target_user': owner.name or str(owner.uuid),
        'target_item': item.name or str(item.uuid),
        'job_id': job_id,
    }


@api_actions_router.post(
    '/rebuild_computed_tags_for_all',
    summary='Recalculate all computed tags for all users',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_computed_tags_for_all(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    database: Annotated[db_interfaces.AbsDatabase, Depends(dep.get_database)],
    misc_repo: Annotated[db_interfaces.AbsMiscRepo, Depends(dep.get_misc_repo)],
):
    """Recalculate all computed tags for all users."""
    use_case = actions_use_cases.RebuildKnownTagsForAllUseCase(database, misc_repo)

    try:
        operation_id = await use_case.execute(user)
    except Exception as exc:
        return web.response_from_exc(exc)

    return {
        'result': 'rebuilding known tags for all users',
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/copy_image/{source_item_uuid}/to/{target_item_uuid}',
    summary='Copy image from one item to another',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | list[str]],
)
async def api_action_copy_image(
    user: Annotated[models.User, Depends(dep.get_current_user)],
    database: Annotated[db_interfaces.AbsDatabase, Depends(dep.get_database)],
    misc_repo: Annotated[db_interfaces.AbsMiscRepo, Depends(dep.get_misc_repo)],
    users_repo: Annotated[db_interfaces.AbsUsersRepo, Depends(dep.get_users_repo)],
    items_repo: Annotated[db_interfaces.AbsItemsRepo, Depends(dep.get_items_repo)],
    meta_repo: Annotated[db_interfaces.AbsMetaRepo, Depends(dep.get_meta_repo)],
    object_storage: Annotated[os_interfaces.AbsObjectStorage, Depends(dep.get_object_storage)],
    source_item_uuid: UUID,
    target_item_uuid: UUID,
):
    """Copy image from one item to another.

    This will invoke copying of content, preview and a thumbnail.
    """
    use_case = actions_use_cases.CopyImageUseCase(
        database, misc_repo, users_repo, items_repo, meta_repo, object_storage
    )

    try:
        media_types = await use_case.execute(
            user=user,
            source_uuid=source_item_uuid,
            target_uuid=target_item_uuid,
        )
    except Exception as exc:
        return web.response_from_exc(exc)

    return {'result': 'Copying image', 'will_copy': media_types}
