"""Computationally heavy operations."""
from typing import Annotated

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.actions import actions_api_models
from omoide.omoide_api.actions import actions_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

api_actions_router = APIRouter(prefix='/actions', tags=['Actions'])


@api_actions_router.post(
    '/rebuild_known_tags',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str | None],
)
async def api_action_rebuild_known_tags(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    target: actions_api_models.RebuildKnownTagsInput,
    background_tasks: BackgroundTasks,
):
    """Recalculate all known tags for user.

    If given user UUID is null, recalculation will be done for anon user.
    """
    use_case = actions_use_cases.RebuildKnownTagsUseCase(mediator)

    try:
        user, job_id = await use_case.pre_execute(admin, target.user_uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    background_tasks.add_task(use_case.execute, admin, user, job_id)
    return {
        'result': 'Rebuilding known tags',
        'target_user': user.name if user else 'anon',
        'job_id': job_id,
    }


@api_actions_router.post(
    '/rebuild_computed_tags',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, int | str | None],
)
async def api_action_rebuild_computed_tags(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    target: actions_api_models.RebuildComputedTagsInput,
    background_tasks: BackgroundTasks,
):
    """Recalculate all computed tags for specific user.

    As a starting point we will take root item for this user.
    If `including_children` is set to True, this will also affect all
    descendants of the item. This operation potentially can take a lot of time.
    """
    use_case = actions_use_cases.RebuildComputedTagsUseCase(mediator)

    try:
        owner, item, job_id = await use_case.pre_execute(admin,
                                                         target.user_uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    if item is not None:
        background_tasks.add_task(use_case.execute, admin, item,
                                  job_id, target.including_children)
        return {
            'result': 'Rebuilding computed tags',
            'target_user': owner.name or str(owner.uuid),
            'target_item': item.name or str(item.uuid),
            'job_id': job_id,
        }

    return {
        'result': 'Nothing to rebuild',
        'target_user': owner.name or str(owner.uuid),
        'target_item': None,
        'job_id': job_id,
    }


@api_actions_router.post(
    '/copy_image',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str | list[str]],
)
async def api_action_copy_image(
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    target: actions_api_models.CopyContentInput,
):
    """Copy image from one item to another.

    This will invoke copying of content, preview and a thumbnail.
    """
    use_case = actions_use_cases.CopyImageUseCase(mediator)

    try:
        media_types = await use_case.execute(
            user=user,
            source_uuid=target.source_item_uuid,
            target_uuid=target.target_item_uuid,
        )
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'result': 'Copying image',
        'will_copy': media_types,
    }
