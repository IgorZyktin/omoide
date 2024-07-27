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

actions_router = APIRouter(prefix='/actions', tags=['Actions'])


@actions_router.post(
    '/rebuild_known_tags',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict[str, str],
)
async def api_action_rebuild_known_tags(
    admin: Annotated[models.User, Depends(dep.get_admin_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
    target: actions_api_models.RebuildTagsInput,
    background_tasks: BackgroundTasks,
):
    """Recalculate all known tags for anon user."""
    use_case = actions_use_cases.RebuildKnownTagsUseCase(mediator)

    try:
        target_user, job_id = await use_case.pre_execute(admin,
                                                         target.user_uuid)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    if target_user is None:
        name = 'anon'
    else:
        name = target_user.name

    background_tasks.add_task(use_case.execute, admin, target_user, job_id)
    return {'result': f'Rebuilding known tags for user {name}'}
