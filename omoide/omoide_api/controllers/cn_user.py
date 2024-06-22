"""Personal information about current user.
"""
import http

from fastapi import APIRouter
from fastapi import Depends

from omoide import domain
from omoide import utils
from omoide.infra.mediator import Mediator
from omoide.omoide_api import use_cases
from omoide.omoide_api.controllers import models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

user_router = APIRouter(prefix='/user', tags=['user'])


@user_router.get(
    '/stats',
    status_code=http.HTTPStatus.OK,
    response_model=models.UserStatsOutput,
)
async def api_get_user_stats(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get statistics for current user."""
    use_case = use_cases.GetCurrentUserStatsUseCase(mediator)

    try:
        output = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)

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
async def api_get_user_tags(
    user: domain.User = Depends(dep.get_current_user),
    mediator: Mediator = Depends(dep.get_mediator),
):
    """Get all known tags for current user."""
    use_case = use_cases.GetCurrentUserTagsUseCase(mediator)

    try:
        tags = await use_case.execute(user)
    except Exception as exc:
        web.raise_from_exc(exc)

    return tags
