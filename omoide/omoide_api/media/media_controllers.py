"""Media related API operations."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import models
from omoide.infra.mediator import Mediator
from omoide.omoide_api.media import media_api_models
from omoide.omoide_api.media import media_use_cases
from omoide.presentation import dependencies as dep
from omoide.presentation import web

media_router = APIRouter(prefix='/media', tags=['Media'])


@media_router.post(
    '/{item_uuid}',
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, str],
)
async def api_create_media(
    item_uuid: UUID,
    media: media_api_models.MediaInput,
    user: Annotated[models.User, Depends(dep.get_known_user)],
    mediator: Annotated[Mediator, Depends(dep.get_mediator)],
):
    """Create new media record.

    This endpoint allows you to load content.
    """
    use_case = media_use_cases.CreateMediaUseCase(mediator)

    try:
        raw_media = models.RawMedia(**media.model_dump())
        media_id = await use_case.execute(user, item_uuid, raw_media)
    except Exception as exc:
        web.raise_from_exc(exc)
        raise  # INCONVENIENCE - Pycharm does not recognize NoReturn

    return {
        'media_id': media_id,
        'result': f'Created Media with id={media_id} for item {item_uuid}',
    }
