"""Computationally heavy operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import dependencies as dep
from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.actions import actions_use_cases
from omoide.presentation import web

api_actions_router = APIRouter(prefix='/actions', tags=['Actions'])


@api_actions_router.post(
    '/rebuild_known_tags_anon',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_known_tags_anon(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Recalculate all known tags for anon user."""
    use_case = actions_use_cases.RebuildKnownTagsForAnonUseCase(mediator)

    try:
        operation_id = await use_case.execute(admin)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'rebuilding known tags for anon',
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/rebuild_known_tags_user/{user_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_known_tags_user(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    user_uuid: UUID,
):
    """Recalculate all known tags for registered user."""
    use_case = actions_use_cases.RebuildKnownTagsForUserUseCase(mediator)

    try:
        operation_id = await use_case.execute(admin, user_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'rebuilding known tags for user',
        'user_uuid': str(user_uuid),
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/rebuild_known_tags_all',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str],
)
async def api_action_rebuild_known_tags_all(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Recalculate all known tags for registered user."""
    use_case = actions_use_cases.RebuildKnownTagsForAllUseCase(mediator)

    try:
        operation_id = await use_case.execute(admin)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'rebuilding known tags for all users',
        'operation_id': operation_id,
    }


@api_actions_router.post(
    '/rebuild_computed_tags/{item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str | None],
)
async def api_action_rebuild_computed_tags(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    item_uuid: UUID,
):
    """Recalculate all computed tags for specific user.

    If `including_children` is set to True, this will also affect all
    descendants of the item. This operation potentially can take a lot of time.
    """
    use_case = actions_use_cases.RebuildComputedTagsForItemUseCase(mediator)

    try:
        owner, item, job_id = await use_case.execute(admin, item_uuid)
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'Rebuilding computed tags',
        'target_user': owner.name or str(owner.uuid),
        'target_item': item.name or str(item.uuid),
        'job_id': job_id,
    }


@api_actions_router.post(
    '/copy_image/{source_item_uuid}/to/{target_item_uuid}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | list[str]],
)
async def api_action_copy_image(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    source_item_uuid: UUID,
    target_item_uuid: UUID,
):
    """Copy image from one item to another.

    This will invoke copying of content, preview and a thumbnail.
    """
    use_case = actions_use_cases.CopyImageUseCase(mediator)

    try:
        media_types = await use_case.execute(
            user=user,
            source_uuid=source_item_uuid,
            target_uuid=target_item_uuid,
        )
    except Exception as exc:
        return web.raise_from_exc(exc)

    return {
        'result': 'Copying image',
        'will_copy': media_types,
    }
