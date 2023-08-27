"""Media related API operations.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status

from omoide import use_cases
from omoide import utils
from omoide.domain import errors
from omoide.domain import interfaces
from omoide.domain.application import input_models
from omoide.domain.core import core_models
from omoide.presentation import dependencies as dep
from omoide.presentation import web

router = APIRouter(prefix='/api/media')


@router.post('/{uuid}', status_code=status.HTTP_201_CREATED)
async def api_create_media(
        uuid: UUID,
        in_media: input_models.InMedia,
        user: Annotated[core_models.User, Depends(dep.get_known_user)],
        policy: Annotated[interfaces.AbsPolicy, Depends(dep.get_policy)],
        use_case: Annotated[use_cases.CreateMediaUseCase,
                            Depends(dep.create_media_use_case)],
):
    """Create or update media entry."""
    media = core_models.Media(
        id=-1,
        created_at=utils.now(),
        processed_at=None,
        error='',
        owner_uuid=user.uuid,  # type: ignore
        item_uuid=uuid,
        media_type=in_media.media_type,
        content=in_media.get_binary_content(),
        ext=in_media.ext,
    )

    result = await use_case.execute(policy, user, uuid, media)

    if isinstance(result, errors.Error):
        web.raise_from_error(result)

    return {}